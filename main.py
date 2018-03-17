# -*- coding: utf-8 -*-

import redis
from Tkinter import *
import ttk
import time
import thread

R = redis.Redis(host='localhost', port=6379) # change

NAME = { # change
    1: "* 李邦宁 113",
    2: "Umi 445",
    3: "Citrus 339"
}

PROBLEM_NAME = { # change
    1: "A - 蓝色",
    3: "B - 橙色",
}

CONTEST_ID = 1 # change

QUEUE_NAME = "ballon_%d" % CONTEST_ID
BACKUP_QUEUE_NAME = "ballon_bak_%d" % CONTEST_ID
RUNID_FIELD = "runid"
SUBMIT_TIME_FIELD = "submit_time"
STATUS_FIELD = "status"
STATUS_FINISHED = "finished"
STATUS_WAIT = "wait"


def lower_bound(arr, key):
    left = 0
    right = len(arr) - 1
    res = len(arr)
    while left <= right:
        mid = (left + right) >> 1
        if arr[mid] >= key:
            res = mid
            right = mid - 1
        else:
            left = mid + 1
    return res


def get_status_key(user_id, pid):
    return "status_%d_%d" % (user_id, pid)


def get_name(user_id):
    user_id = int(user_id)
    if user_id in NAME:
        return NAME[user_id]
    else:
        return "user: %d" % user_id


def get_problem_color(pid):
    pid = int(pid)
    if pid in PROBLEM_NAME:
        return PROBLEM_NAME[pid]
    else:
        return str(pid)


class PrinterTkinter:
    def __init__(self):
        self.root = Tk()
        self.root.title("气球发放")

        self.runid_to_node = dict()
        self.runid_to_uid = dict()
        self.runid_to_pid = dict()
        self.have_uid_pid = set()
        self.unfinished_runid = []

        self.frame_left_top = Frame(width=400, height=200)
        self.frame_right_top = Frame(width=400, height=200)
        self.frame_center = Frame(width=800, height=400)
        self.frame_bottom = Frame(width=800, height=50)

        # 定义左上方区域
        self.left_top_title = Label(self.frame_left_top, text="发放状态:", font=('Arial', 25))
        self.left_top_title.grid(row=0, column=0, columnspan=2, sticky=NSEW, padx=50, pady=30)

        self.var_finish = StringVar()
        self.var_wait = StringVar()

        self.left_top_frame = Frame(self.frame_left_top)
        self.left_top_frame_left1 = Label(self.frame_left_top, text="已发放", font=('Arial', 20))
        self.left_top_frame_left2 = Label(self.frame_left_top, textvariable=self.var_finish, font=('Arial', 15))
        self.var_finish.set(0)
        self.left_top_frame_right1 = Label(self.frame_left_top, text="未发放", font=('Arial', 20))
        self.left_top_frame_right2 = Label(self.frame_left_top, textvariable=self.var_wait, font=('Arial', 15))
        self.var_wait.set(0)
        self.left_top_frame_left1.grid(row=1, column=0)
        self.left_top_frame_left2.grid(row=1, column=1)
        self.left_top_frame_right1.grid(row=2, column=0)
        self.left_top_frame_right2.grid(row=2, column=1)

        # 定义右上方区域
        self.var_entry = StringVar()

        self.right_top_title = Label(self.frame_right_top, text="切换状态(输入runid)：", font=('Arial', 20))
        self.right_top_entry = Entry(self.frame_right_top, textvariable=self.var_entry)

        self.number = int
        self.right_top_button = Button(self.frame_right_top, text="确定", command=self.button_switch, font=('Arial', 15))
        self.right_top_title.grid(row=0, column=0)
        self.right_top_entry.grid(row=1, column=0)
        self.right_top_button.grid(row=2, column=0, padx=20, pady=20)


        # 定义中心列表区域
        self.tree = ttk.Treeview(self.frame_center, show="headings", height=18, columns=("a", "b", "c", "d", "e"))
        self.vbar = ttk.Scrollbar(self.frame_center, orient=VERTICAL, command=self.tree.yview)
        # 定义树形结构与滚动条
        self.tree.configure(yscrollcommand=self.vbar.set)

        # 表格的标题
        self.tree.column("a", width=50, anchor="center")
        self.tree.column("b", width=150, anchor="center")
        self.tree.column("c", width=150, anchor="center")
        self.tree.column("d", width=200, anchor="center")
        self.tree.column("e", width=150, anchor="center")
        self.tree.heading("a", text="Runid")
        self.tree.heading("b", text="User")
        self.tree.heading("c", text="Problem")
        self.tree.heading("d", text="Time")
        self.tree.heading("e", text="Status")

        # 调用方法获取表格内容插入
        self.get_tree()
        self.tree.grid(row=0, column=0, sticky=NSEW)
        self.vbar.grid(row=0, column=1, sticky=NS)

        # 整体区域定位
        self.frame_left_top.grid(row=0, column=0, padx=2, pady=5)
        self.frame_right_top.grid(row=0, column=1, padx=30, pady=30)
        self.frame_center.grid(row=1, column=0, columnspan=2, padx=4, pady=5)
        self.frame_bottom.grid(row=2, column=0, columnspan=2)

        self.frame_left_top.grid_propagate(0)
        self.frame_right_top.grid_propagate(0)
        self.frame_center.grid_propagate(0)
        self.frame_bottom.grid_propagate(0)

        thread.start_new_thread(self.listen, ())
        self.root.mainloop()

    # 表格内容插入
    def get_tree(self):
        bak_list = R.lrange(BACKUP_QUEUE_NAME, 0, -1)
        for bak in bak_list:
            bak = bak.split('_')
            uid = int(bak[0])
            pid = int(bak[1])
            runid = int(bak[2])
            self.runid_to_uid[runid] = uid
            self.runid_to_pid[runid] = pid
            if R.hget(get_status_key(uid, pid), RUNID_FIELD) == None:
                R.hset(get_status_key(uid, pid), RUNID_FIELD, runid)
                status = STATUS_WAIT
                R.hset(get_status_key(uid, pid), STATUS_FIELD, status)
                submit_time = time.ctime()
                R.hset(get_status_key(uid, pid), SUBMIT_TIME_FIELD, submit_time)
                self.have_uid_pid.add("%d_%d" % (uid, pid))
            elif "%d_%d" % (uid, pid) in self.have_uid_pid:
                continue
            else:
                status = R.hget(get_status_key(uid, pid), STATUS_FIELD)
                submit_time = R.hget(get_status_key(uid, pid), SUBMIT_TIME_FIELD)
                self.have_uid_pid.add("%d_%d" % (uid, pid))

            if status == STATUS_FINISHED:
                self.var_finish.set(int(self.var_finish.get()) + 1)
                pos = "end"
            else:
                self.var_wait.set(int(self.var_wait.get()) + 1)
                pos = lower_bound(self.unfinished_runid, runid)
                self.unfinished_runid.insert(pos, runid)

            node = self.tree.insert("", str(pos), values=(runid, get_name(uid), get_problem_color(pid), submit_time, status))
            self.runid_to_node[runid] = node

    def button_switch(self):
        self.number = self.right_top_entry.get()
        runid = int(self.right_top_entry.get())
        if not (runid in self.runid_to_node):
            return
        self.tree.delete(self.runid_to_node[runid])
        uid = self.runid_to_uid[runid]
        pid = self.runid_to_pid[runid]
        status_before = R.hget(get_status_key(uid, pid), STATUS_FIELD)
        submit_time = R.hget(get_status_key(uid, pid), SUBMIT_TIME_FIELD)
        if status_before == STATUS_WAIT:
            status = STATUS_FINISHED
            R.hset(get_status_key(uid, pid), STATUS_FIELD, STATUS_FINISHED)
        else:
            status = STATUS_WAIT
            R.hset(get_status_key(uid, pid), STATUS_FIELD, STATUS_WAIT)

        if status == STATUS_FINISHED:
            pos = lower_bound(self.unfinished_runid, runid)
            self.unfinished_runid.pop(pos)
            pos = "end"
        else:
            pos = lower_bound(self.unfinished_runid, runid)
            self.unfinished_runid.insert(pos, runid)
        node = self.tree.insert("", str(pos), values=(runid, get_name(uid), get_problem_color(pid), submit_time, status))

        if status == STATUS_WAIT:
            self.var_wait.set(int(self.var_wait.get()) + 1)
            self.var_finish.set(int(self.var_finish.get()) - 1)
        else:
            self.var_wait.set(int(self.var_wait.get()) - 1)
            self.var_finish.set(int(self.var_finish.get()) + 1)
        R.hset(get_status_key(uid, pid), STATUS_FIELD, status)
        self.runid_to_node[runid] = node

    def listen(self):
        while True:
            msg = R.blpop(QUEUE_NAME, 0)[1]
            R.rpush(BACKUP_QUEUE_NAME, msg)
            bak = msg.split('_')
            uid = int(bak[0])
            pid = int(bak[1])
            runid = int(bak[2])
            self.runid_to_uid[runid] = uid
            self.runid_to_pid[runid] = pid
            if R.hget(get_status_key(uid, pid), RUNID_FIELD) == None:
                R.hset(get_status_key(uid, pid), RUNID_FIELD, runid)
                status = STATUS_WAIT
                R.hset(get_status_key(uid, pid), STATUS_FIELD, status)
                submit_time = time.ctime()
                R.hset(get_status_key(uid, pid), SUBMIT_TIME_FIELD, submit_time)
                self.have_uid_pid.add("%d_%d" % (uid, pid))
            elif "%d_%d" % (uid, pid) in self.have_uid_pid:
                continue
            else:
                status = R.hget(get_status_key(uid, pid), STATUS_FIELD)
                submit_time = R.hget(get_status_key(uid, pid), SUBMIT_TIME_FIELD)
                self.have_uid_pid.add("%d_%d" % (uid, pid))

            if status == STATUS_FINISHED:
                self.var_finish.set(int(self.var_finish.get()) + 1)
                pos = "end"
            else:
                self.var_wait.set(int(self.var_wait.get()) + 1)
                pos = lower_bound(self.unfinished_runid, runid)
                self.unfinished_runid.insert(pos, runid)

            node = self.tree.insert("", str(pos),
                                    values=(runid, get_name(uid), get_problem_color(pid), submit_time, status))
            self.runid_to_node[runid] = node


if __name__ == '__main__':
    PrinterTkinter()