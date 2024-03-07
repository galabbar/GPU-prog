import subprocess
import pynvml as nvml
import psutil
from devicedata import *
from threading import Thread
import time
from plot import *

repeats = 4

def get_avg(arr):
    n = len(arr)
    res = sum(arr)
    return round(res / n, 3) if n > 0 else 0

def run_function(BGP, function, data_list, time_list, HORP):

    while BGP.poll() is None:
        try:
            function(HORP, data_list)
            if len(time_list) == 0:
                time_list.append(time_interval)
            else:
                time_list.append(time_list[-1] + time_interval)
        except:
            break

        time.sleep(time_interval)

# def record_time_intervals(BGP, data_list):

#     while BGP.poll() is None:
#         data_list.append(data_list[-1] + time_interval)
#         time.sleep(time_interval)

def main_task(device_index=0):
    nvml.nvmlInit()
    handle = nvml.nvmlDeviceGetHandleByIndex(device_index)

    gpu_util, cpu_util, ram, mem = [], [], [], []
    Results = {}

    for i in range(repeats):
        GPU_memory_usage_data_list, GPU_usage_data_list, CPU_usage_data_list, RAM_usage_data_list = [], [], [], []
        GPU_memory_time, GPU_usage_time, CPU_usage_time, RAM_usage_time = [], [], [], [] #[0], [0], [0], [0]
        # time_interval_data_list = [time_interval]

        print("============ Running the background process ============")

        bgp = subprocess.Popen("./cuda_prog.exe")
        process = psutil.Process(bgp.pid)

        t1 = Thread(target=run_function, args=(bgp, measure_current_GPU_usage_per_handle, GPU_usage_data_list, GPU_usage_time, handle))
        t2 = Thread(target=run_function, args=(bgp, measure_current_GPU_memory_per_handle, GPU_memory_usage_data_list, GPU_memory_time, handle))
        t3 = Thread(target=run_function, args=(bgp, measure_current_CPU_usage_percent_per_pid, CPU_usage_data_list, CPU_usage_time, process))
        t4 = Thread(target=run_function, args=(bgp, measure_current_RAM_usage_per_pid, RAM_usage_data_list, RAM_usage_time, process))
        # t5 = Thread(target=record_time_intervals, args=(bgp, time_interval_data_list))

        t1.start()
        t2.start()
        t3.start()
        t4.start()
        # t5.start()
        t1.join()
        t2.join()
        t3.join()
        t4.join()
        # t5.join()

        GPU_memory_usage_data_list = [round(x, 3) for x in GPU_memory_usage_data_list]
        GPU_usage_data_list = [round(x, 3) for x in GPU_usage_data_list]
        CPU_usage_data_list = [round(x, 3) for x in CPU_usage_data_list]
        RAM_usage_data_list = [round(x, 3) for x in RAM_usage_data_list]

        Results[i] = {
                      "GPU-mem": (GPU_memory_usage_data_list, GPU_memory_time),
                      "GPU-util": (GPU_usage_data_list, GPU_usage_time),
                      "CPU-util": (CPU_usage_data_list, CPU_usage_time),
                      "RAM-util": (RAM_usage_data_list, RAM_usage_time)
                    }

        print(f"CPU USAGE: {CPU_usage_data_list}")
        print(f"RAM USAGE: {RAM_usage_data_list}")
        print(f"GPU USAGE: {GPU_usage_data_list}")
        print(f"GPU MEMORY USAGE: {GPU_memory_usage_data_list}")

        print("============ Background process ended ============\n")

        # bgp.terminate()  # Terminate the process after the loop
        bgp.wait()

        print("============ Results ============")
        print(f"GPU utilization avg #{i+1}: {get_avg(GPU_usage_data_list)}")
        print(f"CPU utilization avg #{i+1}: {get_avg(CPU_usage_data_list)}")
        print(f"GPU memory avg #{i+1}: {get_avg(GPU_memory_usage_data_list)}")
        print(f"RAM avg #{i+1}: {get_avg(RAM_usage_data_list)}")
        print("============ End of results ============\n")

        gpu_util.append(get_avg(GPU_usage_data_list))
        cpu_util.append(get_avg(CPU_usage_data_list))
        mem.append(get_avg(GPU_memory_usage_data_list))
        ram.append(get_avg(RAM_usage_data_list))

    print("\n============ Final Results ============\n")
    print(f"GPU utilization avg: {get_avg(gpu_util)}")
    print(f"CPU utilization avg: {get_avg(cpu_util)}")
    print(f"GPU memory avg: {get_avg(mem)}")
    print(f"RAM avg: {get_avg(ram)}")

    avg_results = {"GPU-mem": get_avg(mem),
                   "GPU-util": get_avg(gpu_util),
                   "CPU-util": get_avg(cpu_util),
                   "RAM-util": get_avg(ram)
    }

    return Results, avg_results

if __name__ == "__main__":
    Results, avg_results = main_task()
    dict_keys = ["CPU-util", "GPU-util", "GPU-mem", "RAM-util"]
    X_axis_for_bars = ["CPU Utilization", "GPU utilization", "GPU memory Utilization (MiB)", "RAM utilization"]

    for i in range(repeats):
        for key in dict_keys:

            Y = Results[i][key][0]
            X = Results[i][key][1]

            print(f"Trial {i+1} FOR {key}: X = {X}, Y = {Y}")

            line_graph(X, Y, f"throughput_{key}_trial-{i+1}", save_fig=True, show_fig=False)
    
    for i in range(len(dict_keys)):
        Y = [avg_results[dict_keys[i]]]
        X = [X_axis_for_bars[i]]

        bar_graph(X, Y, f"avg_{dict_keys[i]}", save_fig=True, show_fig=False)
