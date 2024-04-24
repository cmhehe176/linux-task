from asyncio import Task
from process import *
from lib import *
from cpu import *

import time


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
            self.cpu.preQueue[int(args[2])] = [process, ]

        print("Tạo tiến trình thành công: Process {}".format(process.pid))
        print("file excute code: {}".format(args[1]))
        print("")

    def run_cmd(self, cmd):
        """Khởi chạy chương trình mô phỏng

        Args:
            cmd (string): Các tham số cho từ command
        """
        print("============================================================================")
        print(">>>>>>>>>>>>>>>>>>>>>         Start Running         <<<<<<<<<<<<<<<<<<<<<<<<")
        print("============================================================================")
        
        while True:
            print("")
            # Kiểm tra xem còn tiến trình nào trong hệ thống hay không
            if self.cpu.RunQueue.num + self.cpu.WaitQueue.num + len(self.cpu.preQueue) == 0:
                print("============================================================================")
                print(">>>>>>>>>>>>>>>>>>>>>>>      DONE ALL TASK!!!      <<<<<<<<<<<<<<<<<<<<<<<<<")
                print("============================================================================")
                break
            
            print("Time clock:", self.cpu.clock)
            
            # Kiểm tra xem có tiến trình nào muốn tham gia vào tại thời điểm hiện tại không
            if self.cpu.clock in self.cpu.preQueue.keys():
                for process in list(self.cpu.preQueue[self.cpu.clock]):
                    self.cpu.RunQueue.enQueue(Node(process))
                    print("Process {} đến => RunQueue".format(process.pid))
                del self.cpu.preQueue[self.cpu.clock]
                self.cpu.CurTask = self.cpu.RunQueue.header.next.task_struct

            print("RunQueue: Front =>", self.cpu.RunQueue.get_id_process())
            print("WaitQueue: Front =>", self.cpu.WaitQueue.get_id_process())

            # Nếu chỉ còn các tiến trình đang đợi và có yêu cầu I/O, tiếp tục thực hiện I/O
            if self.cpu.WaitQueue.num != 0 and self.cpu.RunQueue.num == 0 and self.cpu.IO_FLAG:
                self.cpu.clock += 1
                self.cpu.wake_up("io.txt")
                time.sleep(1)
                continue

            # In ra thông tin của tiến trình đang chạy
            if self.cpu.CurTask is not None:
                print("Process ID {} || Process counter {} || Running instruction {}".format(self.cpu.CurTask.pid,
                                                                                                self.cpu.CurTask.pc,
                                                                                                self.cpu.CurTask.instrucMem[
                                                                                                    self.cpu.CurTask.pc]))
                # thực thi câu lệnh
                flag = self.cpu.decoder.execute()

                # nếu chạy đến lệnh end => tiến trình hoàn thành  => cần phải tải tiến trình tiếp theo lên nếu có
                if flag == 1:
                    print("Finish Process: Process {}".format(self.cpu.CurTask.pid))
                    print("============================Finish Process {}===============================".format(
                        self.cpu.CurTask.pid))

                    self.cpu.release()
                    self.cpu.scheduler.time_slice = 0
                    self.cpu.rescheduler()
                    self.cpu.pidmanager.removePid(self.cpu.CurTask)  # Thay self.cpu.FinishTask bằng self.cpu.CurTask
                    self.cpu.remove_from_tasklist(self.cpu.CurTask)  # Thay self.cpu.FinishTask bằng self.cpu.CurTask

                # nếu có câu lệnh yêu cầu IO
                elif flag == 2:
                    self.cpu.IO_handle()
                    if self.cpu.RunQueue.num + self.cpu.WaitQueue.num + len(self.cpu.preQueue) == 0:
                        print("done")
                        continue

                # nếu yêu cầu IO vẫn chưa được thỏa mãn
                if self.cpu.IO_FLAG:
                    self.cpu.wake_up("io.txt")

                # hết time slice mà tiến trình vẫn chưa xong và trong RunQueue vẫn còn tiến trình
                if self.cpu.scheduler.time_slice == self.cpu.scheduler.QT_time and self.cpu.RunQueue.num > 1 and flag != 1:
                    print("============================Time Quantum Out===============================")
                    print("============================CONTEXT SWITCH=================================")

                    # Tiến trình FinishTask ở đây được đặt vào
                    self.cpu.scheduler.time_slice = 0
                    self.cpu.CurTask = self.cpu.RunQueue.deQueue().task_struct  # Thay self.cpu.FinishTask bằng self.cpu.CurTask
                    self.cpu.RunQueue.enQueue(Node(self.cpu.CurTask))

                    # Context Switch
                    self.cpu.swap_out(self.cpu.CurTask)  # Thay self.cpu.FinishTask bằng self.cpu.CurTask
                    print("Swap out process: Process {}".format(self.cpu.CurTask.pid))
                    print("stack:", self.cpu.CurTask.stack)
                    print("regis:", self.cpu.CurTask.process_context.register)
                    self.cpu.swap_in(self.cpu.CurTask)
                    print("Swap in process: Process {}".format(self.cpu.CurTask.pid))
                    print("stack:", self.cpu.CurTask.stack)
                    print("regis:", self.cpu.CurTask.process_context.register)
                    print("============================================================================")

            time.sleep(1)

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
            "run": self.run_cmd,
            "boot": self.boot_cmd,
            "create": self.create_cmd,
            "exit": self.exit_cmd
        }
        # Kiểm tra xem lệnh nhập vào có tồn tại trong cmd_lib hay không
        if args[0] in cmd_lib:
            return cmd_lib[args[0]](cmd)
        else:
            print("Lệnh không được hỗ trợ. Vui lòng nhập lại.")
            return 0  # Trả về 0 để không kết thúc chương trình
