# Ballon
Ballon program for NENU-OJ

## 使用说明
### 依赖安装
`$ sudo pip2 install redis`

`$ sudo apt-get install python-tk`

### 运行
`$ python2 main.py --namefile namefile.json --problemfile problemfile.json --redishost 127.0.0.1 --redisport 6379 --contestid 9`

不要打开多个气球程序，应最多只有一个程序连接redis

#### namefile.json
`key`为NENU-OJ的用户ID，`value`为期望展示的用户名
```json
{
  "706": "* ToRapture 113",
  "2": "Umi 445",
  "3": "Citrus 339"
}
```

#### problemfile.json
`key`为NENU-OJ的题目ID，`value`为期望展示的题目名或气球颜色
```json
{
  "1": "A - 蓝色",
  "491": "B - 橙色"
}
```
