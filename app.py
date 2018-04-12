# -*- coding: UTF-8 -*-

from bottle import route, run, template, error, request, post, FormsDict, static_file
import os, time, json, threading, urllib.request, copy

# 获取当前文件执行的路径, 返回基于当前执行文件路径的全路径
def getPath(filename):
    return os.path.dirname(os.path.realpath(__file__)) + os.path.sep + filename

# 格式化json响应内容
def jsonRes(code, msg):
    return json.dumps({'code': code, 'msg': msg})

# 临时的请求缓存内容
data = []
# 原始记录
origin_data = []
# 读取配置文件
with open(getPath('list.json'), 'r', encoding='utf-8') as l:
    data = json.load(l)
    origin_data = copy.deepcopy(data)

# 错误处理
@error(404)
def error404(error):
    return '<h1>您访问的页面不存在!</h1>'
@error(500)
def error500(error):
    return '<h1>您访问的页面出错了!</h1>'

# 静态资源
@route('/static/<path:path>')
def statics(path):
    return static_file(path, getPath('/'))

# 首页
@route('/')
@route('/index')
@route('/index.html')
def index():
    # 读取模板文件
    try: 
        with open(getPath('index.html'), 'r', encoding='utf-8') as tpl:
            return template(tpl.read(), time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime()), data=json.dumps(origin_data))
    except FileNotFoundError:
        pass
    return '<h1>主页模板文件不存在!</h1>'

# 数据列表
@route('/list')
def _list():
    refreshData()
    return json.dumps(data)

# 设置监听列表
@post('/setList')
def set_list():
    params = (FormsDict)(request.params).decode('utf-8')
    if 'list' in params.keys():
        try:
            l = json.loads(params['list'])
            if isinstance(l, list):
                formattedList = []
                for li in l:
                    if 'url' in li:
                        formattedList.append(li)
                with open(getPath('list.json'), 'w', encoding='utf-8') as listJson:
                    listJson.write(json.dumps(formattedList))
                global data, origin_data
                data = formattedList
                origin_data = copy.deepcopy(formattedList)
                return jsonRes(1, '操作成功!')
            else:
                return jsonRes(-1, '内部list参数错误!')
        except json.decoder.JSONDecodeError:
            return jsonRes(-1, '数据解析失败!')

    return jsonRes(-1, '参数错误!')

# 刷新数据
def refreshData():
    for l in data:
        try:
            l['health'] = urllib.request.urlopen(l['url'] + '/health').read().decode('utf-8')
            l['trace'] = urllib.request.urlopen(l['url'] + '/trace').read().decode('utf-8')
            l['metrics'] = urllib.request.urlopen(l['url'] + '/metrics').read().decode('utf-8')
        except BaseException as e:
            # TODO 通知服务器失效
            print(e)

# 检查路径信息
def check_urls():
    while 1:
        refreshData()
        time.sleep(60)

# 多线程轮循获取指定url信息
def start_checking():
    try:
        t = threading.Thread(target=check_urls)
        t.start()
    except:
        print('Error: unable to start thread')

start_checking()
run(host='localhost', port=8080)