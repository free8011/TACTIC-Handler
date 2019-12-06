from thlib.side.Qt import QtWidgets as QtGui
from thlib.side.Qt import QtGui as Qt4Gui
from thlib.side.Qt import QtNetwork
from thlib.side.Qt import QtCore
from thlib.environment import env_inst, env_read_config, env_write_config
import thlib.global_functions as gf
import thlib.tactic_classes as tc
from thlib.ui_classes.ui_custom_qwidgets import Ui_collapsableWidget


class Ui_repoSyncDialog(QtGui.QDialog):
    downloads_finished = QtCore.Signal()
    file_download_done = QtCore.Signal(object)

    def __init__(self, stype, sobject, parent=None):
        super(self.__class__, self).__init__(parent=parent)

        self.stype = stype
        self.sobject = sobject
        self.togglers = [False, False, False, False]
        self.repo_sync_items = []
        self.sync_in_progress = False
        self.interrupted = False
        self.auto_close = False

        self.get_all_presets_from_server()

        self.create_ui()

    def create_ui(self):
        if self.sobject:
            self.setWindowTitle('Sync Repo for: {0}'.format(self.sobject.get_title()))
        else:
            self.setWindowTitle('Sync Repo for: {0}'.format(self.stype.get_pretty_name()))
        self.setSizeGripEnabled(True)

        self.setFocusPolicy(QtCore.Qt.StrongFocus)

        self.create_tree_widget()
        self.fill_presets_combo_box()
        self.fill_tree_widget()
        self.fit_to_content_tree_widget()
        self.create_controls()
        self.controls_actions()

        self.create_download_queue()

        self.resize(650, 550)

        self.readSettings()

    def controls_actions(self):

        self.none_button.clicked.connect(lambda: self.switch_items('none'))
        self.all_process_button.clicked.connect(lambda: self.switch_items('process'))
        self.all_with_builtins_button.clicked.connect(lambda: self.switch_items('builtins'))
        self.all_children_button.clicked.connect(lambda: self.switch_items('children'))

        self.tree_widget.itemChanged.connect(self.check_tree_items)
        self.presets_combo_box.currentIndexChanged.connect(self.apply_repo_sync_preset)

        self.start_sync_button.clicked.connect(self.start_sync_ui)

    def create_download_queue(self):
        self.download_queue = Ui_repoSyncQueueWidget(embedded=True)

        self.download_queue.downloads_finished.connect(self.files_downloads_finished)
        self.download_queue.file_download_done.connect(self.file_download_finished)

        self.grid.addWidget(self.download_queue, 0, 2, 4, 2)

    def files_downloads_finished(self):

        self.sync_in_progress = False

        if not self.interrupted:
            self.downloads_finished.emit()

        if self.auto_close:
            self.close()

        self.downloads_progress_bar.setVisible(False)

    def file_download_finished(self, fl):
        if not self.interrupted:
            self.file_download_done.emit(fl)

            progress = self.downloads_progress_bar.value()
            self.downloads_progress_bar.setValue(progress + 1)
            self.downloads_progress_bar.setFormat(u'%v / %m {}'.format(fl.get_filename_with_ext()))

    def check_tree_items(self, changed_item):
        if len(self.tree_widget.selectedItems()) > 1:
            for item in self.tree_widget.selectedItems():
                item.setCheckState(0, changed_item.checkState(0))

    def switch_items(self, item_type='none'):
        preset_dict = self.get_current_preset_dict()

        if preset_dict:

            if item_type == 'process':
                gf.set_tree_widget_checked_state(
                    self.tree_widget, preset_dict, only_types_tuple=(':{pr}'), state=self.togglers[0]
                )
                self.togglers[0] = not self.togglers[0]

            elif item_type == 'builtins':
                gf.set_tree_widget_checked_state(
                    self.tree_widget, preset_dict, only_types_tuple=(':{b}'), state=self.togglers[1]
                )
                self.togglers[1] = not self.togglers[1]

            elif item_type == 'children':
                gf.set_tree_widget_checked_state(
                    self.tree_widget, preset_dict, only_types_tuple=(':{s}'), state=self.togglers[2]
                )
                self.togglers[2] = not self.togglers[2]

            elif item_type == 'none':
                gf.set_tree_widget_checked_state(
                    self.tree_widget, preset_dict, only_types_tuple=(':{s}', ':{pr}', ':{b}'), state=self.togglers[3]
                )
                self.togglers[3] = not self.togglers[3]

    def create_controls(self):

        self.versionChooserHorizontalLayout = QtGui.QHBoxLayout()
        self.versionChooserHorizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.versionChooserHorizontalLayout.setObjectName("versionChooserHorizontalLayout")

        self.versionlessSyncRadioButton = QtGui.QRadioButton()
        self.versionlessSyncRadioButton.setChecked(True)
        self.versionlessSyncRadioButton.setObjectName("versionlessSyncRadioButton")
        self.versionlessSyncRadioButton.setText('Versionless Sync')

        self.fullSyncRadioButton = QtGui.QRadioButton()
        self.fullSyncRadioButton.setObjectName("fullSyncRadioButton")
        self.fullSyncRadioButton.setText('Full Sync')

        self.versionChooserHorizontalLayout.addWidget(self.versionlessSyncRadioButton)
        self.versionChooserHorizontalLayout.addWidget(self.fullSyncRadioButton)

        self.none_button = QtGui.QPushButton('Toggle All')
        self.none_button.setIcon(gf.get_icon('checkbox-multiple-marked-outline', icons_set='mdi', scale_factor=1))
        self.none_button.setFlat(True)

        self.all_process_button = QtGui.QPushButton('Toggle Process')
        self.all_process_button.setIcon(gf.get_icon('checkbox-blank-circle', icons_set='mdi', scale_factor=0.6))
        self.all_process_button.setFlat(True)

        self.all_with_builtins_button = QtGui.QPushButton('Toggle Builtin Processes')
        self.all_with_builtins_button.setIcon(gf.get_icon('checkbox-blank-circle', icons_set='mdi', scale_factor=0.6))
        self.all_with_builtins_button.setFlat(True)

        self.all_children_button = QtGui.QPushButton('Toggle Children')
        self.all_children_button.setIcon(gf.get_icon('view-sequential', icons_set='mdi', scale_factor=1))
        self.all_children_button.setFlat(True)

        self.togglers_widget = QtGui.QWidget()
        self.togglers_layout = QtGui.QGridLayout()
        self.togglers_layout.setContentsMargins(0, 0, 0, 0)
        self.togglers_layout.setSpacing(6)
        self.togglers_widget.setLayout(self.togglers_layout)

        self.togglers_layout.addWidget(self.none_button, 0, 0, 1, 1)
        self.togglers_layout.addWidget(self.all_process_button, 0, 1, 1, 1)
        self.togglers_layout.addWidget(self.all_with_builtins_button, 1, 0, 1, 1)
        self.togglers_layout.addWidget(self.all_children_button, 1, 1, 1, 1)

        self.togglers_layout.addLayout(self.versionChooserHorizontalLayout, 2, 0, 1, 2)

        # Creating collapsable
        self.controls_collapsable = Ui_collapsableWidget(state=True)
        layout_colapsable = QtGui.QVBoxLayout()
        self.controls_collapsable.setLayout(layout_colapsable)
        self.controls_collapsable.setText('Hide Togglers')
        self.controls_collapsable.setCollapsedText('Show Togglers')
        layout_colapsable.addWidget(self.togglers_widget)

        self.controls_collapsable.collapsed.connect(self.toggle_presets_edit_buttons)

        self.start_sync_button = QtGui.QPushButton('Begin Repo Sync')
        self.start_sync_button.setFlat(True)

        start_sync_color = Qt4Gui.QColor(16, 160, 16)
        start_sync_color_active = Qt4Gui.QColor(16, 220, 16)

        self.start_sync_button.setIcon(gf.get_icon('sync', color=start_sync_color, color_active=start_sync_color_active, icons_set='mdi', scale_factor=1))

        self.progress_bar = QtGui.QProgressBar()
        self.progress_bar.setMaximum(100)
        # self.progressBarLayout.addWidget(self.progressBar)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setHidden(True)

        self.downloads_progress_bar = QtGui.QProgressBar()
        self.downloads_progress_bar.setMaximum(100)
        # self.progressBarLayout.addWidget(self.progressBar)
        self.downloads_progress_bar.setTextVisible(True)
        self.downloads_progress_bar.setHidden(True)

        self.grid.addWidget(self.controls_collapsable, 2, 0, 1, 2)
        self.grid.addWidget(self.start_sync_button, 3, 0, 1, 2)
        self.grid.addWidget(self.progress_bar, 4, 0, 1, 4)
        self.grid.addWidget(self.downloads_progress_bar, 5, 0, 1, 4)

    def toggle_presets_edit_buttons(self, state):

        if state:
            self.add_new_preset_button.setHidden(True)
            self.save_new_preset_button.setHidden(True)
            self.remove_preset_button.setHidden(True)
        else:
            self.add_new_preset_button.setHidden(False)
            self.save_new_preset_button.setHidden(False)
            self.remove_preset_button.setHidden(False)

    def set_auto_close(self, auto_close):
        self.auto_close = auto_close

    def create_tree_widget(self):

        self.grid = QtGui.QGridLayout()
        self.grid.setContentsMargins(9, 9, 9, 9)
        self.grid.setSpacing(6)
        self.setLayout(self.grid)

        self.create_presets_combo_box()

        self.tree_widget = QtGui.QTreeWidget(self)
        self.tree_widget.setTabKeyNavigation(True)
        self.tree_widget.setVerticalScrollMode(QtGui.QAbstractItemView.ScrollPerPixel)
        self.tree_widget.setAllColumnsShowFocus(True)
        self.tree_widget.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
        self.tree_widget.setHeaderHidden(True)
        self.tree_widget.setObjectName('tree_widget')
        self.tree_widget.setAlternatingRowColors(True)
        self.tree_widget.setStyleSheet(gf.get_qtreeview_style())
        self.tree_widget.setRootIsDecorated(True)

        self.grid.addWidget(self.tree_widget, 1, 0, 1, 2)
        self.grid.setRowStretch(1, 1)

    def create_presets_combo_box(self):
        self.grid_presets = QtGui.QGridLayout()

        self.presets_combo_box = QtGui.QComboBox()

        self.add_new_preset_button = QtGui.QToolButton()
        self.add_new_preset_button.setAutoRaise(True)
        self.add_new_preset_button.setIcon(gf.get_icon('plus-box', icons_set='mdi', scale_factor=1.2))
        self.add_new_preset_button.clicked.connect(self.add_new_preset)
        self.add_new_preset_button.setToolTip('Create new Preset and Save (from current state)')
        self.add_new_preset_button.setHidden(True)

        self.save_new_preset_button = QtGui.QToolButton()
        self.save_new_preset_button.setAutoRaise(True)
        self.save_new_preset_button.setIcon(gf.get_icon('content-save', icons_set='mdi', scale_factor=1))
        self.save_new_preset_button.clicked.connect(self.save_preset_to_server)
        self.save_new_preset_button.setToolTip('Save Current Preset Changes')
        self.save_new_preset_button.setHidden(True)

        self.remove_preset_button = QtGui.QToolButton()
        self.remove_preset_button.setAutoRaise(True)
        self.remove_preset_button.setIcon(gf.get_icon('delete', icons_set='mdi', scale_factor=1))
        self.remove_preset_button.clicked.connect(self.close)
        self.remove_preset_button.setToolTip('Remove Current Preset')
        self.remove_preset_button.setHidden(True)

        self.grid_presets.addWidget(self.remove_preset_button, 0, 0, 1, 1)
        self.grid_presets.addWidget(self.presets_combo_box, 0, 1, 1, 1)
        self.grid_presets.addWidget(self.save_new_preset_button, 0, 2, 1, 1)
        self.grid_presets.addWidget(self.add_new_preset_button, 0, 3, 1, 1)

        self.grid_presets.setColumnStretch(1, 0)

        self.grid.addLayout(self.grid_presets, 0, 0, 1, 2)

    def fill_presets_combo_box(self, current_preset=None):
        self.presets_combo_box.clear()

        current_idx = 0

        for i, preset in enumerate(self.presets_list):
            self.presets_combo_box.addItem(preset['pretty_preset_name'])
            self.presets_combo_box.setItemData(i, preset['preset_name'])
            if preset['preset_name'] == current_preset:
                current_idx = i

        self.presets_combo_box.setCurrentIndex(current_idx)

    def fill_tree_widget(self):

        self.fill_builtin_processes()
        self.fill_stype_pipeline(self.stype)
        self.fill_children_pipelines_and_processes(self.stype)

    def fill_builtin_processes(self, parent_tree_item=None):
        if not parent_tree_item:
            parent_tree_item_add = self.tree_widget.addTopLevelItem
        else:
            parent_tree_item_add = parent_tree_item.addChild

        # Builtin processes
        for key in ['publish', 'attachment', 'icon']:
            top_item = QtGui.QTreeWidgetItem()
            top_item.setText(0, key.capitalize() + ' (builtin)')
            top_item.setCheckState(0, QtCore.Qt.Checked)
            top_item.setData(1, 0, '{0}:{1}'.format(key, '{b}'))
            parent_tree_item_add(top_item)

    def fill_stype_pipeline(self, stype=None, parent_tree_item=None):
        if not parent_tree_item:
            parent_tree_item_add = self.tree_widget.addTopLevelItem
        else:
            parent_tree_item_add = parent_tree_item.addChild

        if stype.pipeline:
            for stype_pipeline in stype.pipeline.itervalues():
                top_item = QtGui.QTreeWidgetItem()
                title = stype_pipeline.info.get('name')
                if not title:
                    title = stype_pipeline.info.get('code')
                top_item.setText(0, title)
                top_item.setData(1, 0, '{0}:{1}'.format(stype_pipeline.info.get('code'), '{pp}'))
                parent_tree_item_add(top_item)

                for key, val in stype_pipeline.pipeline.items():
                    child_item = QtGui.QTreeWidgetItem()
                    child_item.setText(0, key.capitalize())
                    child_item.setCheckState(0, QtCore.Qt.Checked)
                    child_item.setData(1, 0, '{0}:{1}'.format(key, '{pr}'))

                    item_color = Qt4Gui.QColor(200, 200, 200)
                    process = stype_pipeline.get_pipeline_process(key)
                    if process:
                        hex_color = process.get('color')
                        color = None
                        if hex_color:
                            color = gf.hex_to_rgb(hex_color, tuple=True)
                        if color:
                            item_color = Qt4Gui.QColor(*color)
                    child_item.setIcon(0, gf.get_icon('circle', color=item_color, scale_factor=0.55))

                    top_item.addChild(child_item)
                    top_item.setExpanded(True)

    def fill_children_pipelines_and_processes(self, stype=None, parent_tree_item=None, added_stypes=None):
        if not parent_tree_item:
            parent_tree_item_add = self.tree_widget.addTopLevelItem
        else:
            parent_tree_item_add = parent_tree_item.addChild

        if not added_stypes:
            added_stypes = []

        # Children process
        if stype.schema:
            for child in stype.schema.children:
                child_stype = stype.get_project().stypes.get(child['from'])
                relationship_type = child.get('type')
                if child_stype and relationship_type not in ['many_to_many']:

                    top_item = QtGui.QTreeWidgetItem()
                    top_item.setText(0, child_stype.get_pretty_name() + ' (child)')
                    top_item.setCheckState(0, QtCore.Qt.Checked)
                    top_item.setData(1, 0, '{0}:{1}'.format(child_stype.get_code(), '{s}'))

                    clr = child_stype.get_stype_color(tuple=True)
                    stype_color = None
                    if clr:
                        stype_color = Qt4Gui.QColor(clr[0], clr[1], clr[2], 255)
                    top_item.setIcon(0, gf.get_icon('view-sequential', color=stype_color, icons_set='mdi', scale_factor=1.1))

                    parent_tree_item_add(top_item)

                    self.fill_builtin_processes(top_item)

                    # breaking recursion
                    if child_stype not in added_stypes:
                        added_stypes.append(child_stype)

                        self.fill_stype_pipeline(child_stype, top_item)

                        self.fill_children_pipelines_and_processes(child_stype, top_item, added_stypes)

    def fit_to_content_tree_widget(self):

        items_count = 0
        for item in QtGui.QTreeWidgetItemIterator(self.tree_widget):
            if item.value().isExpanded():
                items_count += 1

        row_height = items_count * self.tree_widget.sizeHintForRow(0) + 500
        mouse_pos = Qt4Gui.QCursor.pos()
        self.setGeometry(mouse_pos.x(), mouse_pos.y(), 450, row_height)

    def add_new_preset(self):

        add_preset_dialog = QtGui.QDialog(self)
        add_preset_dialog.setWindowTitle('Save as new Preset {}'.format(self.stype.get_pretty_name()))
        add_preset_dialog.setMinimumSize(320, 80)
        add_preset_dialog.setMaximumSize(450, 80)

        add_preset_dialog_layout = QtGui.QVBoxLayout()
        add_preset_dialog.setLayout(add_preset_dialog_layout)

        add_preset_dialog_line_edit = QtGui.QLineEdit('New Preset')

        add_preset_dialog_button = QtGui.QPushButton('Create and Save')

        add_preset_dialog_layout.addWidget(add_preset_dialog_line_edit)
        add_preset_dialog_layout.addWidget(add_preset_dialog_button)

        add_preset_dialog_button.clicked.connect(lambda: self.save_preset_to_server(
            preset_name=add_preset_dialog_line_edit.text().lower().replace(' ', '_'),
            pretty_preset_name=add_preset_dialog_line_edit.text()
        ))
        add_preset_dialog_button.clicked.connect(add_preset_dialog.close)

        add_preset_dialog.exec_()
        # self.fill_presets_combo_box()

    def get_current_preset_name(self):
        current_index = self.presets_combo_box.currentIndex()
        return self.presets_combo_box.itemData(current_index)

    def get_current_preset_dict(self):
        preset_dict = self.get_preset_config(self.get_current_preset_name(), json=False)
        return preset_dict['data']

    def get_preset_dict_by_type(self, type='pipeline', preset_dict=None, only_enabled=False):
        result_preset_dict = {}

        if type == 'pipeline':
            for name, preset in preset_dict.items():
                if name.endswith(':{pp}'):
                    result_preset_dict[name.replace(':{pp}', '')] = preset

        if type == 'builtin':
            for name, preset in preset_dict.items():
                if name.endswith(':{b}'):
                    if only_enabled:
                        if preset['state']:
                            result_preset_dict[name.replace(':{b}', '')] = preset
                    else:
                        result_preset_dict[name.replace(':{b}', '')] = preset

        if type == 'process':
            for name, preset in preset_dict.items():
                if name.endswith(':{pr}'):
                    if only_enabled:
                        if preset['state']:
                            result_preset_dict[name.replace(':{pr}', '')] = preset
                    else:
                        result_preset_dict[name.replace(':{pr}', '')] = preset

        if type == 'child':
            for name, preset in preset_dict.items():
                if name.endswith(':{s}'):
                    if only_enabled:
                        if preset['state']:
                            result_preset_dict[name.replace(':{s}', '')] = preset
                    else:
                        result_preset_dict[name.replace(':{s}', '')] = preset

        return result_preset_dict

    def apply_repo_sync_preset(self, current_index=None, preset_name=None):

        if not preset_name:
            preset_name = self.presets_combo_box.itemData(current_index)

        preset_dict = self.get_preset_by_name(preset_name)

        if preset_dict:
            # Pipeline items should not have check state, filter it with {pp} tag
            gf.set_tree_widget_checked_state(self.tree_widget, preset_dict, ignore_types_tuple=(':{pp}'))

    def get_preset_by_name(self, preset_name):
        # Only used on initial items filling
        if self.presets_list:
            for preset in self.presets_list:
                if preset['preset_name'] == preset_name:
                    return preset

    def get_all_presets_from_server(self):

        server = tc.server_start()

        key = 'search_type:{0}'.format(self.stype.get_code())

        search_type = 'sthpw/wdg_settings'

        project_code = self.stype.get_project().get_code()

        filters = [('key', 'like', '{0}%'.format(key)), ('project_code', project_code)]
        columns = ['data']

        presets = server.query(search_type, filters, columns)

        if not presets:
            self.presets_list = [
                {
                    'pretty_preset_name': 'Default',
                    'preset_name': 'default',
                }
            ]
        else:

            new_presets_list = []
            for preset in presets:
                new_presets_list.append(gf.from_json(preset['data']))

            self.presets_list = new_presets_list

    def get_preset_config(self, preset_name=None, pretty_preset_name=None, json=True):

        if not preset_name:
            preset_name = 'default'

        if not pretty_preset_name:
            pretty_preset_name = preset_name.capitalize().replace('_', ' ')

        # Preparing preset data
        preset_dict = {
            'preset_name': preset_name,
            'pretty_preset_name': pretty_preset_name,
        }
        gf.get_tree_widget_checked_state(self.tree_widget, preset_dict)

        key = 'search_type:{0}:preset_name:{1}'.format(self.stype.get_code(), preset_name)

        if json:
            data_dict = gf.to_json(preset_dict)
        else:
            data_dict = preset_dict

        data = {
            'data': data_dict,
            'key': key,
            'login': 'admin',
            'project_code': self.stype.get_project().get_code(),
        }

        return data

    def add_file_objects_to_queue(self, files_objects_list):
        for file_object in files_objects_list:
            self.repo_sync_items.append(self.download_queue.schedule_file_object(file_object))

    def get_presets_list(self):
        return self.presets_list

    def download_files(self):

        self.downloads_progress_bar.setVisible(True)

        if not self.interrupted:
            for repo_sync_item in self.repo_sync_items:
                repo_sync_item.download()
                self.download_queue.files_num_label.setText(
                    str(self.download_queue.files_queue_tree_widget.topLevelItemCount())
                )

            self.downloads_progress_bar.setMaximum(len(self.repo_sync_items))

        if not self.repo_sync_items:
            self.files_downloads_finished()

    def clear_queue(self):
        self.download_queue.clear_queue()
        self.repo_sync_items = []

    @env_inst.async_engine
    def start_sync(self, preset_dict=None):
        self.sync_in_progress = True
        # it is recommended to use finished signal
        if not preset_dict:
            preset_dict = self.get_current_preset_dict()

        self.clear_queue()
        self.sobject.update_snapshots()

        self.sync_by_pipeline(self.sobject, preset_dict)
        self.sync_children(self.sobject, preset_dict)

        self.download_files()

    def start_sync_ui(self, preset_dict=None):

        self.show()

        self.sync_in_progress = True
        self.progress_bar.setHidden(False)

        self.clear_queue()
        if not preset_dict:
            preset_dict = self.get_current_preset_dict()

        if self.sobject:
            self.sobject.update_snapshots()
            self.sync_by_pipeline(self.sobject, preset_dict)
            self.sync_children(self.sobject, preset_dict)
            self.save_last_sync_date()
        else:
            stype_sobjects, data = tc.get_sobjects_new(
                self.stype.get_code(),
                [],
                project_code=self.stype.project.get_code(),
                get_all_snapshots=True
            )
            for sobject in stype_sobjects.values():
                self.sync_by_pipeline(sobject, preset_dict)
                self.sync_children(sobject, preset_dict)
                self.save_last_sync_date(sobject)

        self.download_files()
        self.progress_bar.setHidden(True)

    def interrupt_sync_process(self):
        self.interrupted = True

    def sync_by_pipeline(self, sobject=None, preset_dict=None):
        if not sobject:
            sobject = self.sobject

        if not preset_dict:
            preset_dict = self.get_current_preset_dict()

        current_pipeline_preset_dict = self.get_preset_dict_by_type('pipeline', preset_dict)
        current_builtin_preset_dict = self.get_preset_dict_by_type('builtin', preset_dict, True)

        if current_pipeline_preset_dict:
            for pipeline_name, preset in current_pipeline_preset_dict.items():
                self.sync_by_sobject(sobject, preset.get('sub'), current_builtin_preset_dict)
        elif current_builtin_preset_dict:
            self.sync_by_sobject(sobject, {}, current_builtin_preset_dict)

    @env_inst.async_engine
    def sync_children(self, sobject=None, preset_dict=None):
        stype = sobject.get_stype()

        if not preset_dict:
            preset_dict = self.get_current_preset_dict()

        children_preset_dict = self.get_preset_dict_by_type('child', preset_dict, True)
        project_obj = stype.get_project()

        for child_code, children_preset in children_preset_dict.items():
            related_sobjects, query_info = yield env_inst.async_task(sobject.get_related_sobjects, child_stype=project_obj.stypes.get(child_code), parent_stype=stype, get_all_snapshots=True)

            if related_sobjects:
                for related_sobject in related_sobjects.values():
                    self.sync_by_pipeline(related_sobject, children_preset.get('sub'))
                    self.sync_children(related_sobject, children_preset.get('sub'))

                    total = query_info['total_sobjects_query_count']
                    self.progress_bar.setMaximum(total)
                    progress = self.progress_bar.value()
                    self.progress_bar.setValue(progress + 1)
                    self.progress_bar.setFormat(u'%v / %m {}'.format(related_sobject.get_title()))

    def sync_by_sobject(self, sobject=None, sync_preset_dict=None, builtin_preset_dict=None):

        process_objects = sobject.get_all_processes()
        enabled_processes = self.get_preset_dict_by_type('process', sync_preset_dict, True)

        versionless_list = []
        versions_list = []
        if builtin_preset_dict:
            all_precesses = dict(enabled_processes.items() + builtin_preset_dict.items())
        else:
            all_precesses = enabled_processes

        for process_name, process_object in process_objects.items():

            if not self.interrupted:

                if process_name in all_precesses.keys():
                    contexts = process_object.get_contexts()
                    for context, context_obj in contexts.items():

                        versionless_snapshots = context_obj.get_versionless()
                        for code, snapshot in versionless_snapshots.items():
                            versionless_list.extend(snapshot.get_files_objects())

                        versions_snapshots = context_obj.get_versions()
                        for code, snapshot in versions_snapshots.items():
                            versions_list.extend(snapshot.get_files_objects())

        if self.versionlessSyncRadioButton.isChecked():
            self.add_file_objects_to_queue(versionless_list)
        else:
            self.add_file_objects_to_queue(versionless_list)
            self.add_file_objects_to_queue(versions_list)

    def save_preset_to_server(self, preset_name=None, pretty_preset_name=None):

        if not preset_name:
            idx = self.presets_combo_box.currentIndex()
            preset_name = self.presets_combo_box.itemData(idx)

        server = tc.server_start()

        data = self.get_preset_config(preset_name, pretty_preset_name)
        search_type = 'sthpw/wdg_settings'

        # Checking for existing key
        filters = [('key', data['key'])]
        columns = ['code', 'project']

        widget_settings = server.query(search_type, filters, columns, single=True)

        if widget_settings:
            code = widget_settings['code']
            project = widget_settings['project']
            search_key = server.build_search_key(search_type, code, project)

            server.insert_update(search_key, data, triggers=False)
        else:
            server.insert(search_type, data, triggers=False)

        self.get_all_presets_from_server()
        self.fill_presets_combo_box(preset_name)

    def get_settings_dict(self):
        settings_dict = {
            'presets_combo_box': self.presets_combo_box.currentIndex(),
        }
        return settings_dict

    def set_settings_from_dict(self, settings_dict=None):
        if not settings_dict:
            settings_dict = {
                'presets_combo_box': 0,
            }

        initial_index = self.presets_combo_box.currentIndex()

        self.presets_combo_box.setCurrentIndex(int(settings_dict.get('presets_combo_box')))

        if initial_index == int(settings_dict.get('presets_combo_box')):
            self.apply_repo_sync_preset(initial_index)

    def save_last_sync_date(self, sobject=None):

        if not sobject:
            sobject = self.sobject

        group_path = 'ui_search/{0}/{1}/{2}/sobjects_conf'.format(
            self.stype.project.info['type'],
            self.stype.project.info['code'],
            self.stype.get_code().split('/')[1]
        )

        current_datetime = QtCore.QDateTime.currentDateTime()
        env_write_config(
            current_datetime.toString('yyyy.MM.dd hh:mm:ss'),
            filename=sobject.get_code(),
            unique_id=group_path,
            long_abs_path=True
        )

    def readSettings(self):
        group_path = 'ui_search/{0}/{1}/{2}'.format(
            self.stype.project.info['type'],
            self.stype.project.info['code'],
            self.stype.get_code().split('/')[1]
        )
        self.set_settings_from_dict(
            env_read_config(
                filename='repo_sync',
                unique_id=group_path,
                long_abs_path=True
            )
        )

    def writeSettings(self):
        group_path = 'ui_search/{0}/{1}/{2}'.format(
            self.stype.project.info['type'],
            self.stype.project.info['code'],
            self.stype.get_code().split('/')[1]
        )
        env_write_config(
            self.get_settings_dict(),
            filename='repo_sync',
            unique_id=group_path,
            long_abs_path=True
        )

    def closeEvent(self, event):
        if not self.sync_in_progress:
            self.writeSettings()
            self.deleteLater()
            event.accept()
        else:
            buttons = (('Ok', QtGui.QMessageBox.NoRole), ('Interrupt', QtGui.QMessageBox.ActionRole))
            reply = gf.show_message_predefined(
                title='Download in Progress',
                message='Some files are not yet Downloaded.\nInterrupt the Sync Process?.',
                buttons=buttons,
                parent=self,
                message_type='question',
            )

            if reply == QtGui.QMessageBox.ActionRole:
                self.interrupt_sync_process()
                self.deleteLater()
                event.accept()
            else:
                event.ignore()


class Ui_repoSyncQueueWidget(QtGui.QMainWindow):
    downloads_finished = QtCore.Signal()
    file_download_done = QtCore.Signal(object)

    def __init__(self, embedded=False, parent=None):
        super(self.__class__, self).__init__(parent=parent)

        self.embedded = embedded

        self.queue_dict = {}
        self.total_downloading_count = 0
        self.total_downloaded_count = 0
        self.network_manager = QtNetwork.QNetworkAccessManager(self)
        self.network_manager.finished.connect(self.network_manager_finished)

        if self.embedded:
            self.create_embedded_ui()
        else:
            self.create_ui()

    def create_ui(self):
        self.setWindowTitle('Repository Sync Queue')

        self.statusbar = QtGui.QStatusBar(self)
        self.statusbar.setObjectName('statusbar')
        self.setStatusBar(self.statusbar)

        self.setWindowFlags(QtCore.Qt.Window)
        self.resize(350, 700)

        self.create_main_layout()
        self.create_controls_layout()

        self.create_controls()
        self.create_tree_widget()

        self.controls_actions()

    def controls_actions(self):
        self.clear_queue_push_button.clicked.connect(self.clear_queue)

    def create_embedded_ui(self):

        self.create_main_layout()
        self.main_layout.setContentsMargins(3, 0, 3, 0)
        self.create_controls_layout()

        self.create_controls()
        self.create_tree_widget()
        self.controls_actions()

    def create_main_layout(self):
        self.central_widget = QtGui.QWidget(self)
        self.central_widget.setObjectName('central_widget')

        self.main_layout = QtGui.QGridLayout(self.central_widget)
        self.main_layout.setContentsMargins(9, 9, 9, 9)
        self.main_layout.setSpacing(0)
        self.main_layout.setObjectName('main_layout')

        self.central_widget.setLayout(self.main_layout)
        self.setCentralWidget(self.central_widget)

    def create_controls_layout(self):
        self.controls_layout = QtGui.QGridLayout()
        self.controls_layout.setContentsMargins(0, 0, 0, 0)
        self.controls_layout.setSpacing(6)
        self.controls_layout.setObjectName('controls_layout')

        self.main_layout.addLayout(self.controls_layout, 0, 0, 1, 1)

    def create_controls(self):

        self.clear_queue_push_button = QtGui.QPushButton('Clear Queue')
        self.clear_queue_push_button.setMinimumSize(QtCore.QSize(120, 0))
        self.clear_queue_push_button.setObjectName('clear_queue_push_button')
        self.clear_queue_push_button.setIcon(gf.get_icon('delete', icons_set='mdi'))
        self.clear_queue_push_button.setFlat(True)

        self.files_count_label = QtGui.QLabel('Downloads in Queue: ')
        self.files_count_label.setObjectName('files_count_label')

        self.files_num_label = QtGui.QLabel('')
        self.files_num_label.setObjectName("files_num_label")

        self.controls_layout.addWidget(self.files_count_label, 0, 0)
        self.controls_layout.addWidget(self.files_num_label, 0, 1)
        self.controls_layout.addWidget(self.clear_queue_push_button, 0, 2)

    def create_tree_widget(self):
        self.files_queue_tree_widget = QtGui.QTreeWidget()
        self.files_queue_tree_widget.setMinimumSize(QtCore.QSize(300, 0))
        self.files_queue_tree_widget.setRootIsDecorated(False)
        self.files_queue_tree_widget.setHeaderHidden(True)
        self.files_queue_tree_widget.setObjectName('files_queue_tree_widget')
        self.files_queue_tree_widget.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
        self.files_queue_tree_widget.setStyleSheet(gf.get_qtreeview_style())
        self.main_layout.addWidget(self.files_queue_tree_widget)

    def create_progress_bar_widget(self):

        self.progress_bar_widget = QtGui.QProgressBar()
        self.progress_bar_widget.setTextVisible(True)
        self.progress_bar_widget.setVisible(True)
        self.progress_bar_widget.setHidden(True)
        self.statusbar.addPermanentWidget(self.progress_bar_widget)

    def set_progress_indicator_on(self):
        self.progress_bar_widget.setHidden(False)

    def set_progress_indicator_off(self):
        self.progress_bar_widget.setHidden(True)
        self.statusbar.showMessage('')

    def set_progress(self, progress, info_dict):
        self.progress_bar_widget.setMaximum(info_dict['total_count'])
        self.statusbar.showMessage(info_dict['status_text'])
        self.progress_bar_widget.setValue(progress + 1)
        if self.progress_bar_widget.maximum() == progress + 1:
            self.set_progress_indicator_off()

    def clear_queue(self):
        self.files_queue_tree_widget.clear()
        self.queue_dict = {}
        self.files_num_label.setText('')
        self.total_downloaded_count = 0
        self.total_downloading_count = 0

    def remove_item_from_queue(self, commit_item=None):

        self.queue_list.remove(commit_item)
        commit_item.close()
        commit_item.deleteLater()
        self.files_queue_tree_widget.takeTopLevelItem(self.files_queue_tree_widget.currentIndex().row())
        self.check_queue()

    def network_manager_finished(self, reply):
        file_object = reply.request().attribute(QtNetwork.QNetworkRequest.User)

        if reply.error() == QtNetwork.QNetworkReply.NoError:
            self.do_download_file_object(file_object, reply)
        else:
            repo_sync_item = self.queue_dict.get(file_object.get_unique_id())
            repo_sync_item.set_download_failed()

    def emit_if_all_downloads_done(self):
        if self.total_downloading_count == self.total_downloaded_count:
            self.downloads_finished.emit()

    def do_download_file_object(self, file_object, reply):
        repo_sync_item = self.queue_dict.get(file_object.get_unique_id())

        info_dict = {
            'status_text': 'Downloading File',
            'total_count': 4
        }
        repo_sync_item.download_progress(3, info_dict)

        full_abs_path = file_object.prepare_repo()
        with open(full_abs_path, "wb") as downloaded_file:
            downloaded_file.write(reply.readAll())

        repo_sync_item.download_progress(4, info_dict)

        downloaded_file.close()
        repo_sync_item.set_download_finished()

        reply.deleteLater()

    def increment_downloaded(self, fl=None):
        self.total_downloaded_count += 1
        self.emit_if_all_downloads_done()

        self.file_download_done.emit(fl)

    def schedule_file_object(self, file_object):
        self.total_downloading_count += 1

        repo_sync_item = gf.add_repo_sync_item(self.files_queue_tree_widget, file_object)

        self.queue_dict[file_object.get_unique_id()] = repo_sync_item

        repo_sync_item.set_network_manager(self.network_manager)

        self.files_queue_tree_widget.scrollToBottom()

        repo_sync_item.downloaded.connect(self.increment_downloaded)

        return repo_sync_item
