from process import *     
from lib import *    
from cpu import *
import time
import numpy as np

class Shell:
    """Mô phỏng shell dùng để xử lý là chạy các lệnh do người dùng nhập
    """
    def __init__(self, cpu=None):
        """Khỏi tạo Shell

        Args:
            cpu (CPU, optional): CPU được sử dụng để thực hiện các lệnh trên shell. Defaults to None.
        """
        self.cpu = cpu
    
    def boot_cmd(self, cmd):
        """Khởi tạo CPU cho quá trình mô phỏng

        Args:
            cmd (string): Các tham số cho từ command
        """
        args = cmd.split(" ")
        self.cpu = CPU(int(args[1]))
        # self.cpu.pidmanager = EnhancedPIDmanager(self.cpu.pidmanager.max)  # Sau khi khởi tạo self.cpu, mới gán pidmanager
        print("Khởi tạo CPU - Ok")
        print("Khởi tạo Decoder - Ok")
        print("Khởi tạo Scheduler Round Robin - ok")
        print("Time Quantum: {}".format(args[1]))
        print("")
    
    def create_cmd(self, cmd):
        """Khởi tạo tiến trình

        Args:
            cmd (string): Các tham số cho từ command
        """
        args = cmd.split(" ")
        process = task_struct(state=TASK_STATE["READY"],
                              excute_code=args[1],
                              arrival_time=int(args[2]))
        self.cpu.pidmanager.createPid(process)
        if int(args[2]) in self.cpu.preQueue.keys():
            self.cpu.preQueue[int(args[2])].append(process)
        else:
            self.cpu.preQueue[int(args[2])] = [process,]

        print("Tạo tiến trình thành công: Process {}".format(process.pid))
        print("file excute code: {}".format(args[1]))
        print("PID: {}".format(process.pid))
        print("")
    
    def run_cmd(self, cmd):
        """Khởi chạy chương trình mô phỏng

        Args:
            cmd (string): Các tham số cho từ command
        """
        print("============================================================================")
        print(">>>>>>>>>>>>>>>>>>>>>         Start Running         <<<<<<<<<<<<<<<<<<<<<<<<")
        print("============================================================================")
        while(1):
            print("")
            # Nếu không còn tiến trình nào trong hệ thống thì sẽ kết thúc mô phỏng
            if self.cpu.RunQueue.num + self.cpu.WaitQueue.num + len(self.cpu.preQueue) == 0:
                print("============================================================================")
                print(">>>>>>>>>>>>>>>>>>>>>>>      DONE ALL TASK!!!      <<<<<<<<<<<<<<<<<<<<<<<<<")
                print("============================================================================")
                # In kết quả thống kê cuối cùng trước khi kết thúc                 
                self.calculate_and_print_statistics()                 
                break
            print("Time clock:", self.cpu.clock)

            # Kiểm tra hàng đợi xem có tiến trình nào đến             
            if self.cpu.clock in self.cpu.preQueue.keys():                 
                while self.cpu.preQueue[self.cpu.clock]:                    
                    process = self.cpu.preQueue[self.cpu.clock].pop(0)                     
                if self.cpu.CurTask is None:                         
                    self.cpu.RunQueue.enQueue(Node(process))                         
                    self.cpu.CurTask = process                    
                else:                         
                    self.cpu.LateArrivalQueue.enQueue(Node(process))                     
                    print(f"Process {process.pid} đến => {'RunQueue' if self.cpu.CurTask == process else 'LateArrivalQueue'}")   
                                  
                del self.cpu.preQueue[self.cpu.clock]

            print("RunQueue: Fontier =>", self.cpu.RunQueue.get_id_process())             
            print("WaitQueue: Fontier =>", self.cpu.WaitQueue.get_id_process())             
            print("LateArrivalQueue:", self.cpu.LateArrivalQueue.get_id_process()) 

            finished_task = None 
            # Kiểm tra LateArrivalQueue sau mỗi lần hết time quantum hoặc khi cpu rảnh             
            while self.cpu.LateArrivalQueue.num > 0 and (self.cpu.LateArrivalQueue.header.next.task_struct.arrival_time <= self.cpu.clock or self.cpu.CurTask is None):                 
                late_process = self.cpu.LateArrivalQueue.deQueue().task_struct                 
                self.cpu.RunQueue.enQueue(Node(late_process))                 
                print(f"Process {late_process.pid} moved from LateArrivalQueue to RunQueue.")                
                # Nếu CPU đang rảnh, gán tiến trình mới cho CPU                 
                if self.cpu.CurTask is None:                     
                    self.cpu.CurTask = late_process  

            # Theo dõi thời gian bắt đầu thực thi             
            if self.cpu.CurTask is not None and self.cpu.CurTask.start_time is None:                 
                self.cpu.CurTask.start_time = self.cpu.clock  
        
            # Nếu tiến chỉ còn tiến trình đang đợi thì sẽ tiếp tục đợi IO
            if self.cpu.WaitQueue.num !=0 and self.cpu.RunQueue.num == 0 and self.cpu.IO_FLAG:
                self.cpu.clock = self.cpu.clock + 1
                self.cpu.wake_up("io.txt")
                time.sleep(1)
                continue

            # In ra thông tin tiến trình đang chạy
            if self.cpu.CurTask is not None and self.cpu.CurTask.pc < len(self.cpu.CurTask.instrucMem):
                print("Process ID {} || Process counter {} || Running instructer {}".format(self.cpu.CurTask.pid,
                                                                                            self.cpu.CurTask.pc,
                                                                                            self.cpu.CurTask.instrucMem[self.cpu.CurTask.pc],
                                                                                            self.cpu.clock))
            #thực thi câu lệnh
                flag = self.cpu.decoder.excute()
            else:                 
                print("Không có tiến trình đang chạy")

            #nếu chạy đến lệnh end => tiến trình hoàn thành  => cần phải tải tiến trình tiếp theo lên nếu có
            if flag == 1 or (self.cpu.CurTask is not None and self.cpu.CurTask.pc >= len(self.cpu.CurTask.instrucMem)):  
                finished_task = self.cpu.CurTask  # Lưu trữ tiến trình đã hoàn thành
                print("Finish Process: Process {}".format(self.cpu.CurTask.pid))
                print("============================Finish Process {}===============================".format(self.cpu.CurTask.pid))
                
                self.cpu.release()
                self.cpu.scheduler.time_slice = 0
                self.cpu.rescheduler()
                self.cpu.pidmanager.removePid(self.cpu.FinishTask)
                self.cpu.remove_from_tasklist(self.cpu.FinishTask)
            
            #  Xử lý sau khi chuyển đổi ngữ cảnh hoặc kết thúc tiến trình             
            if finished_task is not None:                 
                finished_task.finish_time = self.cpu.clock                 
                finished_task.waiting_time += self.cpu.clock - finished_task.start_time                 
                print("Finish Process: Process {}".format(finished_task.pid))                 
                print("============================Finish Process {}===============================".format(finished_task.pid))
            # nếu có câu lệnh yêu cầu IO
            elif flag == 2:
                self.cpu.IO_handle()
                if self.cpu.RunQueue.num + self.cpu.WaitQueue.num + len(self.cpu.preQueue) == 0:
                    print("done")
                    continue

            # Kiểm tra và xử lý hoàn thành I/O             
            if self.cpu.io_done:                 
                wakeup_task = self.cpu.WaitQueue.deQueue().task_struct                 
                wakeup_task.state = TASK_STATE["READY"]                 
                self.cpu.RunQueue.enQueue(Node(wakeup_task))                 
                print("===> Wake up process: Process {}".format(wakeup_task.pid))                 
                self.cpu.io_done = False  # Reset io_done         

            # nếu yêu cầu IO vẫn chưa được thỏa mãn
            if self.cpu.IO_FLAG:
                self.cpu.wake_up("io.txt")
            
            # Thêm thời gian chuyển đổi vào clock             
            if self.cpu.num_context_switches > 0:                 
                self.cpu.clock += self.cpu.total_context_switch_time                 
                self.cpu.total_context_switch_time = 0 # Reset total_context_switch_time sau khi cộng vào clock                 
                self.cpu.num_context_switches = 0

            # Nếu tiến chỉ còn tiến trình đang đợi thì sẽ tiếp tục đợi IO
            if self.cpu.WaitQueue.num != 0 and self.cpu.RunQueue.num == 0:
                self.cpu.clock += 1
                time.sleep(1)
                continue

            # hết time slice mà tiến trình vẫn chưa xong và trong RunQueue vẫn còn tiến trình
            if self.cpu.scheduler.time_slice == self.cpu.scheduler.QT_time and self.cpu.RunQueue.num > 1 and flag != 1:
                print("============================Time Quantum Out===============================")
                print("============================CONTEXT SWITCH=================================")
                
                # Tiến trình FinishTask ở đây được đặt vào
                self.cpu.scheduler.time_slice = 0
                self.cpu.FinishTask = self.cpu.RunQueue.deQueue().task_struct
                self.cpu.CurTask = self.cpu.RunQueue.header.next.task_struct
                self.cpu.RunQueue.enQueue(Node(self.cpu.FinishTask))
                
                # Context Switch
                self.cpu.swap_out(self.cpu.FinishTask)
                print("Swap out process: Process {}".format(self.cpu.FinishTask.pid))
                print("stack:",self.cpu.FinishTask.stack)
                print("regis:",self.cpu.FinishTask.process_context.register)
                self.cpu.swap_in(self.cpu.CurTask)
                print("Swap in process: Process {}".format(self.cpu.CurTask.pid))
                print("stack:",self.cpu.CurTask.stack)
                print("regis:",self.cpu.CurTask.process_context.register)
                print("============================================================================")

            #  # Thêm thời gian chuyển đổi vào clock             
            # if self.cpu.num_context_switches > 0:                 
            #     self.cpu.clock += self.cpu.total_context_switch_time                 
            #     self.cpu.total_context_switch_time = 0 # Reset total_context_switch_time sau khi cộng vào clock                 
            #     self.cpu.num_context_switches = 0    # Reset num_context_switches sau khi cộng vào clock

            # if self.cpu.context_switch_history:
            #     last_switch = self.cpu.context_switch_history.pop()
            #     switch_time = last_switch["switch_time"]
            #     switch_process_id = last_switch["process"]
            #     self.cpu.clock += switch_time
            #     print(f"Context switch from process {switch_process_id}, added {switch_time:.6f} to clock. New time: {self.cpu.clock}")
            # Thêm thời gian chuyển đổi ngữ cảnh vào clock
            # if self.cpu.context_switch_history:
            #     last_switch = self.cpu.context_switch_history.pop()  # Lấy thông tin chuyển đổi cuối cùng
            #     switch_time = last_switch["switch_time"]
            #     switch_process_id = last_switch["process"]
            #     self.cpu.clock += switch_time
            #     print(f"Context switch from process {switch_process_id}, added {switch_time:.6f} to clock. New time: {self.cpu.clock}")

            time.sleep(1)
        self.cpu.context_switch_history.clear()

    def calculate_and_print_statistics(self):
        # Phân tích hiệu suất sau khi mô phỏng kết thúc             
        if self.cpu.context_switch_history:  # Kiểm tra xem có dữ liệu chuyển đổi ngữ cảnh không             
            switch_times = [entry["switch_time"] for entry in self.cpu.context_switch_history]             
            avg_switch_time = sum(switch_times) / len(switch_times)            
            min_switch_time = min(switch_times)             
            max_switch_time = max(switch_times)             
            std_dev_switch_time = np.std(switch_times)             
            print("\nContext Switch Performance Analysis:")  
            print(f"  Number switches: {len(self.cpu.context_switch_history):}") 
            print(f"  Average switch time: {avg_switch_time:.6f} seconds")            
            print(f"  Minimum switch time: {min_switch_time:.6f} seconds")             
            print(f"  Maximum switch time: {max_switch_time:.6f} seconds")            
            print(f"  Standard deviation: {std_dev_switch_time:.6f} seconds") 
    
    def exit_cmd(self, cmd):
        """Thực hiện lệnh exit thoát khỏi chương trình

        Args:
            cmd (string): Các tham số cho từ command

        Returns:
            int: trả về 1 để đánh dấu cho chương trình kêt thúc
        """
        print("log out")
        return 1
    
    def excute_cmd(self, cmd):
        """Thực hiện các lệnh shell được người dùng nhập vào

        Args:
            cmd (string): Lệnh Shell được sử dụng

        Returns:
            int: Tín hiệu thông báo nếu trả về 1 (exit) thì chương trình mô phỏng sẽ kết thúc 
        """
        args = cmd.split(" ")
        cmd_lib = {
            "run":self.run_cmd,
            "boot": self.boot_cmd,
            "create": self.create_cmd,
            "exit": self.exit_cmd
        }
        return cmd_lib[args[0]](cmd) 
    