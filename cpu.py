from lib import *
from process import *
from decode import *
from sched import * 
from collections import deque
import time 

class CPU:
    """Mô phỏng một CPU với bộ lập dịch, bộ decoder và các hàng đợi
    """
    def __init__(self, QTtime, maxPID = 100):
        """Khởi tạo CPU

        Args:
            QTtime (string): Time quantum cho bộ lập lịch Round Robin
            maxPID (int, optional): [description]. Defaults to 100.
        """
        self.clock = 0
        self.pidmanager = PIDmanager(maxPID)
        self.decoder = Decoder(self)
        self.register = { "_R1":0,
                          "_R2":0,
                          "_R3":0,
                          "_R4":0}
        self.task_list = []
        self.RunQueue = Queue()
        self.WaitQueue = Queue()
        self.preQueue = dict()
        self.FinishTask = None
        self.scheduler = Scheduler(QTtime)
        self.CurTask = None
        self.IO_FLAG = 0
        self.context_switch_count = 0
        self.context_switch_times = []
        self.io_done = False
        # Khởi tạo LateArrivalQueue
        self.LateArrivalQueue = Queue() 
        self.num_context_switches = 0   # Thêm thuộc tính này
        self.total_context_switch_time = 0.0
        self.context_switch_history = []
        self.finished_tasks = []  # Thêm thuộc tính này

    # def rescheduler(self):
    #     """Tái lập lịch khi tiến trình hoàn thành hoặc hết time quantum."""
    #     self.FinishTask = self.RunQueue.deQueue().task_struct if self.RunQueue.num != 0 else None
    #     # if self.RunQueue.num != 0:
    #     if self.RunQueue.num != 0 or self.FinishTask is not None:  # Kiểm tra nếu có chuyển đổi
    #         # start_time = time.perf_counter()  # Bắt đầu đo thời gian
    #         print("============================CONTEXT SWITCH=================================")
    #         print("------------------------------------------------------------------------")
    #         # self.swap_out(self.FinishTask) if self.FinishTask is not None else None
    #         print("Load process: Process", self.CurTask.pid)
    #         print("Swap in: Process", self.RunQueue.header.next.task_struct.pid)
    #         print("stack:", self.RunQueue.header.next.task_struct.stack)
    #         print("regis:", self.RunQueue.header.next.task_struct.process_context.register)
    #         self.swap_in(self.RunQueue.header.next.task_struct)
    #         print("------------------------------------------------------------------------")
    #         print("===========================================================================")
    #         # end_time = time.perf_counter()  # Kết thúc đo thời gian
    #         # switch_time = end_time - start_time
    #         # self.context_switch_history.append({"process": self.CurTask.pid, "switch_time": switch_time})
    #         # self.num_context_switches += 1
    #         # self.total_context_switch_time += switch_time

    #     self.CurTask = self.RunQueue.header.next.task_struct if self.RunQueue.num != 0 else None  # Sửa lỗi ở đây

    #     # Corrected line
    #     if self.FinishTask is not None:
    #         self.pidmanager.removePid(self.FinishTask)  # Remove the extra 'cpu.' 
    #         self.remove_from_tasklist(self.FinishTask)
    #         self.finished_tasks.append(self.FinishTask)
    # def rescheduler(self):
    #     """Tái lập lịch khi tiến trình hoàn thành hoặc hết time quantum."""
    #     self.FinishTask = self.RunQueue.deQueue().task_struct if self.RunQueue.num != 0 else None

    #     if self.RunQueue.num != 0 or self.FinishTask is not None:  # Kiểm tra nếu có chuyển đổi
    #         start_time = time.perf_counter()  # Bắt đầu đo thời gian
    #         self.swap_out(self.FinishTask) if self.FinishTask is not None else None

    #         # Chỉ swap_in khi có tiến trình trong RunQueue
    #         if self.RunQueue.num != 0:
    #             print("============================CONTEXT SWITCH=================================")
    #             print("------------------------------------------------------------------------")
    #             print("Load process: Process", self.CurTask.pid)
    #             print("Swap in: Process", self.RunQueue.header.next.task_struct.pid)
    #             print("stack:", self.RunQueue.header.next.task_struct.stack)
    #             print("regis:", self.RunQueue.header.next.task_struct.process_context.register)
    #             self.swap_in(self.RunQueue.header.next.task_struct)
    #             print("------------------------------------------------------------------------")
    #             print("===========================================================================")

    #         end_time = time.perf_counter()  # Kết thúc đo thời gian
    #         switch_time = end_time - start_time
    #         self.context_switch_history.append({"process": self.CurTask.pid, "switch_time": switch_time})
    #         self.num_context_switches += 1
    #         self.total_context_switch_time += switch_time

    #     self.CurTask = self.RunQueue.header.next.task_struct if self.RunQueue.num != 0 else None  # Sửa lỗi ở đây

    #     # Corrected line
    #     if self.FinishTask is not None:
    #         self.pidmanager.removePid(self.FinishTask)  # Remove the extra 'cpu.' 
    #         self.remove_from_tasklist(self.FinishTask)
    #         self.finished_tasks.append(self.FinishTask)

    def rescheduler(self):
        """Tái lập lịch khi tiến trình hoàn thành hoặc hết time quantum."""
        self.FinishTask = self.RunQueue.deQueue().task_struct if self.RunQueue.num != 0 else None

        if self.RunQueue.num != 0:  # Chỉ chuyển đổi ngữ cảnh khi có tiến trình trong RunQueue
            start_time = time.perf_counter()  # Bắt đầu đo thời gian

            if self.FinishTask is not None:  # Nếu có tiến trình kết thúc, swap out trước
                self.swap_out(self.FinishTask)

            # Tiếp tục swap in tiến trình mới
            print("============================CONTEXT SWITCH=================================")
            print("------------------------------------------------------------------------")
            print("Load process: Process", self.CurTask.pid)
            print("Swap in: Process", self.RunQueue.header.next.task_struct.pid)
            print("stack:", self.RunQueue.header.next.task_struct.stack)
            print("regis:", self.RunQueue.header.next.task_struct.process_context.register)
            self.swap_in(self.RunQueue.header.next.task_struct)
            print("------------------------------------------------------------------------")
            print("===========================================================================")
            
            end_time = time.perf_counter()  # Kết thúc đo thời gian
            switch_time = end_time - start_time
            self.context_switch_history.append({"process": self.CurTask.pid, "switch_time": switch_time})
            self.num_context_switches += 1
            self.total_context_switch_time += switch_time

        self.CurTask = self.RunQueue.header.next.task_struct if self.RunQueue.num != 0 else None

        # Corrected line
        if self.FinishTask is not None:
            self.pidmanager.removePid(self.FinishTask)
            self.remove_from_tasklist(self.FinishTask)
            self.finished_tasks.append(self.FinishTask)
            
    def swap_in(self, process):
        """Cơ chế Swap in trong context switch

        Args:
            process (task_struct)): Tiến trình được swap in
        """
        self.register["_R1"] = process.process_context.register["_R1"]
        self.register["_R2"] = process.process_context.register["_R2"]
        self.register["_R3"] = process.process_context.register["_R3"]
        self.register["_R4"] = process.process_context.register["_R4"]
        
    def swap_out(self, process):
        """Cơ chế Swap out trong context switch

        Args:
            process (task_struct): Tiến trình bị swap out
        """
        process.process_context.register["_R1"] = self.register["_R1"]
        process.process_context.register["_R2"] = self.register["_R2"]
        process.process_context.register["_R3"] = self.register["_R3"]
        process.process_context.register["_R4"] = self.register["_R4"]
    
        start_time = time.time()  
        # Mô phỏng độ trễ
        time.sleep(0.0001)  # Ví dụ: 100 microseconds
        end_time = time.time()
        switch_time = end_time - start_time
        print(f"Context switch out time for Process {process.pid}: {switch_time:.6f} seconds")

        # Lưu lại thông tin chuyển đổi ngữ cảnh
        self.context_switch_history.append({
            "process_id": process.pid,
            "switch_time": switch_time,
            "clock_time": self.clock,  # Thời điểm chuyển đổi theo đồng hồ CPU
        })

        self.total_context_switch_time += switch_time
        self.num_context_switches += 1

    def remove_from_tasklist(self, process):
        """Xóa một tiến trình khỏi TaskList khi nó hoàn thành

        Args:
            process (task_struct): task_struct của tiến trình cần xóa
        """
        for indx ,task in enumerate(self.task_list):
            if task.pid == process.pid:
                self.task_list.pop(indx)
    
    def IO_handle(self):
        """Xử lý tiến trình khi có yêu cầu I/O
        """
        print("------------------------------------------------------------------------")
        print("                                IO request                              ")
        print("------------------------------------------------------------------------")
        print("                Đưa tiến trình Process {} vào WaitQueue                 ".format(self.CurTask.pid))
        self.CurTask.state = TASK_STATE["WAITING"]
        self.RunQueue.deQueue()
        self.WaitQueue.enQueue(Node(self.CurTask))
        self.swap_out(self.CurTask)
        print("Swap out process: Process {}".format(self.CurTask.pid))
        print("stack:",self.CurTask.stack)
        print("regis:",self.CurTask.process_context.register)
        
        if self.RunQueue.num != 0:
            self.CurTask = self.RunQueue.header.next.task_struct
            self.swap_in(self.CurTask)
            print("Swap in process: Process {}".format(self.CurTask.pid))
            print("stack:",self.CurTask.stack)
            print("regis:",self.CurTask.process_context.register)
        else:
            self.CurTask = None
        print("RunQueue:", self.RunQueue.get_id_process())
        print("WaitQueue:", self.WaitQueue.get_id_process())
        print("------------------------------------------------------------------------")

        # Giả sử I/O hoàn thành sau một khoảng thời gian
        time.sleep(2)  # Ví dụ: Chờ 2 giây để mô phỏng I/O
        self.io_done = True  # Đánh dấu I/O đã hoàn thành

    def release(self):
        """Giải phóng thanh ghi khi tiến trình chạy xong
        """
        self.register["_R1"] = 0
        self.register["_R2"] = 0
        self.register["_R3"] = 0
        self.register["_R4"] = 0
    
    def wake_up(self, io_file):
        """Đánh thưc tiến trình dậy khi IO được thỏa mãn, io ở đây được mô phỏng thông qua file io.txt

        Args:
            io_file (string): file chứa tín hiệu 
        """
        file = open(io_file, "r")
        lines = file.readlines()
        for line in lines:
            if line == "respone":
                wakeup_task = self.WaitQueue.deQueue().task_struct
                wakeup_task.state = TASK_STATE["RUNNING"]
                print("------------------------------------------------------------------------")
                print("                                IO respone                              ")
                print("===> Wake up process: Process {}".format(wakeup_task.pid))
                self.RunQueue.enQueue(Node(wakeup_task))
                self.CurTask = self.RunQueue.header.next.task_struct
                # self.io_done = True  # Đánh dấu I/O đã hoàn thành
                self.IO_FLAG = 0
                print("------------------------------------------------------------------------")
  
class PIDmanager:
    """Quản lý các giá trị PID
    """
    def __init__(self, maxPid=100):
        self.max = maxPid
        self.max_cur = 0
        self.used_pid = [0]*self.max
    
    def createPid(self, process):
        """Tạo ra thông tin định danh cho tiến trình

        Args:
            process (task_struct): Tiến trình cần cấp phát
        """
        if self.max_cur == self.max:
            process.pid = self.used_pid.index(0)
            self.used_pid[self.used_pid.index(0)] = 1
        else:
            process.pid = self.max_cur
            self.max_cur = self.max_cur + 1
    
    def removePid(self, process):
        self.used_pid[process.pid] = 0
        if self.max_cur == process.pid:
            self.max_cur = self.used_pid.reverse().index(1) - 1 + self.max
            self.used_pid.reverse()