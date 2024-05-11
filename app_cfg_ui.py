import multiprocessing

multiprocessing.freeze_support()
import traceback

from nicegui import app, events, ui
import threading
import time

from local_file_picker import LocalFilePicker

from conf import conf
from conf.conf import log
import logging

# 程序是否在运行
is_running = False
# 战队信息
fight_team_dict = {}
fight_name_options = []
fight_rows = []
bond_name_options = []
bond_rows = []


def run_game():
    global is_running
    try:
        import main
        run_button.enable()
        while (not conf.schedule_check()) and is_running:
            run_button.text = str(conf.schedule_countdown()) + " 后开始"
            time.sleep(1)
        if not is_running:
            return
        run_button.text = '停止'
        from process_control import main_process
        main_process.run()
    except Exception as e:
        log.error("run game error:  " + traceback.format_exc())
    finally:
        is_running = False
        run_button.enable()
        run_button.text = '启动'


def stop_game():
    global is_running
    run_button.text = "停止中..."
    from process_control import main_process
    main_process.stop()
    is_running = False


def start_game():
    global is_running
    run_button.text = "启动中..."
    is_running = True
    threading.Thread(target=run_game).start()


def init_fight_info():
    global fight_rows
    us = conf.get_line_up()
    if len(us) > 0:
        for u in us:
            name = u.get('name')
            talent = u.get('talent')
            order = u.get('order')
            if not name or name == "狗头人矿工":
                continue
            fight_rows.append({'name': name, 'talent': talent, 'order': order})

    global fight_team_dict
    fight_team_dict = conf.get_supported_units()

    global fight_name_options
    fight_names = fight_team_dict.keys()
    if len(fight_rows) == 0:
        fight_name_options = list(fight_names)
    else:
        for name in fight_names:
            have_cfg = False
            for row in fight_rows:
                if row['name'] == name:
                    have_cfg = True
                    break
            if not have_cfg:
                fight_name_options.append(name)


def init_bond_info():
    global bond_rows, bond_name_options, fight_rows
    bond_name_options = []
    bond_rows = conf.get_bond()
    for row in fight_rows:
        bond_name_options.append(row['name'])


def handle_shutdown():
    if is_running:
        stop_game()
    log.warning('程序已退出')


ui.add_head_html('''
    <style>
        .nicegui-content {
            padding: 0;
        }
    </style>
''')
# 账号信息
user = conf.get_user()
init_fight_info()
init_bond_info()
with ui.card().tight().classes('w-full h-screen no-shadow p-0') as card:
    with ui.tabs().classes('w-full h-20') as base_tabs:
        ui.tab('cfg', label='配置与运行', icon='settings').classes('w-1/2')
        ui.tab('log', label='日志', icon='article').classes('w-1/2')
    with ui.tab_panels(base_tabs, value='cfg').classes('w-full h-5/6 mb-auto bg-transparent'):
        # 配置
        with ui.tab_panel('cfg').classes('w-full h-full'):
            with ui.splitter(value=20).classes('w-full h-full') as splitter:
                splitter.set_enabled(False)
                with splitter.before:
                    with ui.tabs().props('vertical').classes('w-full h-full') as cfg_tabs:
                        user_cfg = ui.tab('通用', icon='key')
                        simulator_cfg = ui.tab('模拟器', icon='phone_iphone')
                        fight_cfg = ui.tab('战队', icon='groups')
                        game_cfg = ui.tab('游戏', icon='sports_esports')
                with splitter.after:
                    with ui.tab_panels(cfg_tabs, value=user_cfg).props('vertical').classes(
                            'w-full h-full bg-transparent'):
                        # 账号配置
                        with ui.tab_panel(user_cfg):
                            with ui.row():
                                ui.label("通知设置").style('color: #6E93D6; font-size: 150%; font-weight: 300')
                                with ui.icon('help_outline'):
                                    ui.tooltip('支持将战斗结算信息发送到qq邮箱')
                            with ui.row():
                                ui.input(label='qq邮箱', value=conf.get_mail_receiver(),
                                         on_change=lambda e: conf.set_mail_receiver(e.value)).props('clearable')
                                ui.input(label='授权码', password=True, value=conf.get_mail_code(),
                                         on_change=lambda e: conf.set_mail_code(e.value)).props('clearable')
                                ui.button('获取',
                                          on_click=lambda: ui.open('https://wx.mail.qq.com/list/readtemplate?'
                                                                   'name=app_intro.html#/agreement/authorizationCode',
                                                                   new_tab=True)).style("margin-top: 20px")
                            ui.separator()
                            with ui.row():
                                ui.label("调试").style('color: #6E93D6; font-size: 150%; font-weight: 300')
                            ui.label('日志级别')
                            ui.radio(["DEBUG", "INFO"], value=conf.get_log_level(),
                                     on_change=lambda e: conf.set_log_level(e.value)).props('inline')
                            ui.separator()
                            ui.label('保存截图')
                            ui.switch(value=conf.get_capture_log_switch(),
                                      on_change=lambda e: conf.save_capture_log_switch(e.value)).props("inline")

                        # 模拟器配置
                        with ui.tab_panel(simulator_cfg):
                            with ui.row().classes('w-full'):
                                ui.number(label='模拟器端口号', value=conf.adb_port(), min=0, precision=0,
                                          format='%.0f',
                                          on_change=lambda e: conf.set_adb_port(int(e.value)))
                                with ui.icon('help_outline'):
                                    ui.tooltip('模拟器的adb端口，在模拟器设置中能看到，雷电模拟器是5555').classes(
                                        'bg-sky-900')
                            ui.separator()
                            with ui.row().classes('w-full'):
                                # ui.label("模拟器exe路径")
                                emulator_path = ui.input(label='模拟器exe路径', value=conf.get_emulator_path(),
                                                         on_change=lambda e: conf.set_emulator_path(e.value))
                                with ui.icon('help_outline'):
                                    ui.tooltip('配置模拟器路径后异常退出会自动重启').classes(
                                        'bg-sky-900')


                                async def pick_file() -> None:
                                    result = await LocalFilePicker('~', multiple=True)
                                    emulator_path.value = result[0]


                                ui.button(on_click=pick_file, icon='folder')
                            ui.separator()
                        # 战队配置
                        with ui.tab_panel(fight_cfg):
                            with ui.row():
                                anonymous_switch = ui.switch(text="顺序部署", value=conf.get_anonymous_team(),
                                                             on_change=lambda e: (switch_anonymous(e.value)))
                                with ui.icon('help_outline'):
                                    ui.tooltip(
                                        '顺序部署不用配置战队成员，按照出牌区轮流部署，同时也失去了优先选择战队成员任务等特性').classes(
                                        'bg-sky-900')


                            def switch_anonymous(value):
                                conf.set_anonymous_team(value)
                                team_card.set_visibility(not value)


                            with ui.card() as team_card:
                                ui.separator()
                                team_label = ui.label('战队单位').classes('text-h7')
                                # 出场战队表格
                                fight_columns = [
                                    {'name': 'name', 'label': '单位', 'field': 'name', 'required': True},
                                    {'name': 'talent', 'label': '天赋', 'field': 'talent', 'required': True},
                                    {'name': 'order', 'label': '次序', 'field': 'order', 'required': False},
                                    {'name': 'deleteBtn', 'label': '', 'field': 'deleteBtn', 'required': False},
                                ]

                                with ui.table(columns=fight_columns, rows=fight_rows, row_key='name').classes(
                                        'w-full h-full bg-transparent') as table:
                                    with table.add_slot('bottom-row'):
                                        with table.row():
                                            with table.cell():
                                                fight_name = ui.select(fight_name_options, with_input=True,
                                                                       on_change=lambda event: (
                                                                           fight_talent.set_options(
                                                                               fight_team_dict[
                                                                                   event.value] if event.value else [])
                                                                       ))
                                            with table.cell():
                                                fight_talent = ui.select([])
                                            with table.cell():
                                                fight_order = ui.select([1, 2, 3, 4, -1])
                                            with table.cell():
                                                def add_fight_row() -> None:
                                                    if not fight_name.value or not fight_talent.value:
                                                        ui.notify('单位名和天赋不能为空', type='warning',
                                                                  position='top')
                                                        return
                                                    if len(fight_rows) >= 7:
                                                        ui.notify('最多配置7个单位', type='warning', position='top')
                                                        return
                                                    # 添加战队配置
                                                    table.add_rows(
                                                        {'name': fight_name.value, 'talent': fight_talent.value,
                                                         'order': fight_order.value}
                                                    )

                                                    # 保存战队配置
                                                    conf.set_line_up(fight_rows),
                                                    # 更新单位选项
                                                    fight_name_options[:] = [name for name in fight_name_options if
                                                                             name != fight_name.value]
                                                    fight_name.set_options(fight_name_options)
                                                    refresh_bond_option()

                                                    fight_name.set_value(None)
                                                    fight_talent.set_value(None)
                                                    fight_order.set_value(None)


                                                ui.button(on_click=add_fight_row, icon='person_add').props(
                                                    'flat fab-mini')
                                # 删除Btn
                                table.add_slot('body-cell-deleteBtn', '''
                                    <q-td :props="props">
                                        <q-btn size="sm" color="black" round dense icon="person_remove"
                                            @click="() => $parent.$emit('deleteFightRow', props.row)"
                                        />
                                    </q-td>
                                ''')


                                def delete_fight_row(e: events.GenericEventArguments) -> None:
                                    # 删除战队配置
                                    fight_rows[:] = [row for row in fight_rows if row['name'] != e.args['name']]
                                    # 保存战队配置
                                    conf.set_line_up(fight_rows)
                                    # 更新单位选项
                                    fight_name_options.append(e.args['name'])
                                    refresh_bond_option()
                                    fight_name.set_options(fight_name_options)
                                    fight_name.value = e.args['name']
                                    fight_talent.value = e.args['talent']
                                    table.update()


                                table.on('deleteFightRow', delete_fight_row)
                                ui.separator()

                                # 羁绊配置
                                with ui.row():
                                    bond_label = ui.label('羁绊').classes('text-h7')
                                    with ui.icon('help_outline'):
                                        ui.tooltip(
                                            '羁绊的两个单位需要成对部署:双向关系两者互为依赖，必须一起部署;'
                                            '单向关系是后者跟随前者部署，但前者并不依赖后者。'
                                            '举例来说，现在配置了将军和萨满的双向关系，萨满和锤女的单向关系，那么将军和萨满同时'
                                            '在等待的时候，会等两者能量快满的时候连续放置下将军和萨满，这样萨满的大地之盾一定会给将军。'
                                            '在部署萨满后，会将锤女移动到待部署头部，这样锤女在等待的话会立即跟随萨满部署。以上配置就能实现'
                                            '将军萨满的二连或者将军萨满锤女的三连部署，极大提高刷任务效率。'
                                            '部署次序设为-1，该单位就不上场，适合那些上场没啥用却耗费极大的单位。').classes(
                                            'bg-sky-900')

                                bond_columns = [
                                    {'name': 'former', 'label': '前者', 'field': 'former', 'required': True},
                                    {'name': 'latter', 'label': '后者', 'field': 'latter', 'required': True},
                                    {'name': 'relation', 'label': '关系', 'field': 'relation', 'required': True},
                                    {'name': 'deleteBtn', 'label': '', 'field': 'deleteBtn', 'required': False},
                                ]
                                with ui.table(columns=bond_columns, rows=bond_rows, row_key='former').classes(
                                        'w-full h-full bg-transparent') as bond_table:
                                    with bond_table.add_slot('bottom-row'):
                                        with bond_table.row():
                                            with bond_table.cell():
                                                former = ui.select(bond_name_options)
                                            with bond_table.cell():
                                                latter = ui.select(bond_name_options)
                                            with bond_table.cell():
                                                relation = ui.select(['单向', '双向'])
                                            with bond_table.cell():
                                                def add_bond_row() -> None:
                                                    if not former.value or not latter.value or not relation.value:
                                                        ui.notify('单位名和关系不能为空', type='warning',
                                                                  position='top')
                                                        return
                                                    if former.value == latter.value:
                                                        ui.notify('不能选择相同单位', type='warning',
                                                                  position='top')
                                                        return
                                                    for row in bond_rows:
                                                        if row['former'] == former.value and row[
                                                            'latter'] == latter.value:
                                                            ui.notify('不能重复添加相同单位', type='warning',
                                                                      position='top')
                                                            return
                                                    # 添加羁绊配置
                                                    bond_table.add_rows(
                                                        {'former': former.value, 'latter': latter.value,
                                                         'relation': relation.value}
                                                    )
                                                    # 保存羁绊配置
                                                    conf.set_bond(bond_rows),

                                                    former.set_value(None)
                                                    latter.set_value(None)
                                                    relation.set_value(None)


                                                ui.button(on_click=add_bond_row, icon='group_add').props(
                                                    'flat fab-mini')

                                # 删除Btn
                                bond_table.add_slot('body-cell-deleteBtn', '''
                                    <q-td :props="props">
                                        <q-btn size="sm" color="black" round dense icon="group_remove"
                                            @click="() => $parent.$emit('delete_bond_row', props.row)"
                                        />
                                    </q-td>
                                ''')


                                def delete_bond_row(e: events.GenericEventArguments) -> None:
                                    # 删除羁绊配置
                                    bond_rows[:] = [row for row in bond_rows if row['former'] != e.args['former']
                                                    or row['latter'] != e.args['latter']]
                                    # 保存羁绊配置
                                    conf.set_bond(bond_rows)
                                    # 刷新表格
                                    bond_table.update()


                                bond_table.on('delete_bond_row', delete_bond_row)


                                def refresh_bond_option():
                                    init_bond_info()
                                    former.set_options(bond_name_options)
                                    latter.set_options(bond_name_options)
                            team_card.set_visibility(not conf.get_anonymous_team())

                        with ui.tab_panel(game_cfg):
                            with ui.row().classes('w-full'):
                                ui.label('游戏模式')
                                with ui.icon('help_outline'):
                                    ui.tooltip('自动先做任务，做完后打竞技场').classes(
                                        'bg-sky-900')
                            ui.radio({'pve': '任务', 'pvp': '竞技', '': '自动'}, value=conf.game_mode(),
                                     on_change=lambda e: conf.set_game_mode(e.value)).props('inline')
                            ui.separator()
                            with ui.row().classes('w-full'):
                                ui.label('无限任务')
                                with ui.icon('help_outline'):
                                    ui.tooltip('通过定时修改时区，实现任务无限刷新，可能提高封禁概率').classes(
                                        'bg-sky-900')
                            refresh_switch = ui.switch('', value=conf.is_refresh_task(),
                                                       on_change=lambda e: set_refresh_task(e.value))


                            def set_refresh_task(value):
                                # if value:
                                #     user, passwd = conf.get_user()
                                #     if not user or not passwd or not account.verify(user, passwd):
                                #         refresh_switch.set_value(False)
                                #         ui.notify('当前账号不支持', type='warning', position='top')
                                #         return
                                conf.set_refresh_task(value)


                            ui.separator()

                            with ui.row().classes('w-full'):
                                ui.label('定时运行')
                                with ui.icon('help_outline'):
                                    ui.tooltip(
                                        '在配置时间范围内运行游戏，在配置时间范围外关闭游戏，需要点击运行并保持脚本开启').classes(
                                        'bg-sky-900')
                            with ui.dialog() as start_dialog, ui.card():
                                ui.label('选择开始时间')
                                ui.time(value='08:00', on_change=lambda e: schedule_start_time_event(e.value))
                                ui.button('确认', on_click=start_dialog.close)
                            with ui.dialog() as end_dialog, ui.card():
                                ui.label('选择结束时间')
                                ui.time(value='00:00', on_change=lambda e: schedule_end_time_event(e.value))
                                ui.button('确认', on_click=end_dialog.close)


                            def schedule_switch_event(value):
                                conf.set_schedule_switch(value)
                                start_time.set_visibility(value)
                                end_time.set_visibility(value)
                                sep.set_visibility(value)


                            def schedule_start_time_event(value):
                                conf.set_schedule_start_time(value)
                                start_time.set_text(value)
                                start_time.update()


                            def schedule_end_time_event(value):
                                conf.set_schedule_end_time(value)
                                end_time.set_text(value)
                                start_time.update()


                            with ui.row().classes('w-full'):
                                ui.switch('', value=conf.get_schedule_switch(),
                                          on_change=lambda e: schedule_switch_event(e.value))
                                start_time = ui.button(conf.get_schedule_start_time(), on_click=start_dialog.open)
                                sep = ui.label('至').style('margin-top:5px')
                                end_time = ui.button(conf.get_schedule_end_time(), on_click=end_dialog.open)
                                schedule_switch_event(conf.get_schedule_switch())
                            ui.separator()

                    ui.space()

        # 日志
        with ui.tab_panel('log').classes('w-full h-full bg-transparent'):

            class LogElementHandler(logging.Handler):
                """A log handler that emits messages to a log element."""

                def __init__(self, element: ui.log, level: int = logging.NOTSET) -> None:
                    self.element = element
                    super().__init__(level)
                    self.formatter = logging.Formatter('[%(asctime)s] %(message)s')

                def emit(self, record: logging.LogRecord) -> None:
                    try:
                        msg = self.format(record)
                        self.element.push(msg)
                    except Exception:
                        self.handleError(record)


            log_ui = ui.log(max_lines=10000).classes('w-full h-[300px]').style("color: #6E93D6;")
            log.addHandler(LogElementHandler(log_ui))
            # ui.button('Log time', on_click=lambda: logger.warning(datetime.now().strftime('%X.%f')[:-5]))


    # 启动/停止
    def control_app() -> None:
        run_button.disable()
        if is_running:
            stop_game()
            # ui.notify('程序已停止', type='positive', position='top')
        else:
            # user, passwd = conf.get_user()
            # if not user or not passwd or not account.verify(user, passwd):
            #     ui.notify('验证账号密码失败，试用10分钟', type='warning', position='top')
            start_game()


    run_button = ui.button('启动', on_click=control_app).classes("w-full h-10")

dark = ui.dark_mode()
dark.auto()
app.on_shutdown(handle_shutdown)
app.native.window_args['resizable'] = True
app.native.window_args['title'] = '魔兽自作战'
app.native.start_args['debug'] = False
ui.run(native=True, window_size=(800, 900), reload=False, title="魔兽自作战")
