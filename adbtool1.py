
import customtkinter as ctk
import tkinter as tk
from CTkListbox import *
from CTkToolTip import *
from PIL import Image
import subprocess,os,sys
from time import sleep,time
import matplotlib,wmi
from matplotlib import pyplot as plt
from matplotlib import animation
from win32api import GetSystemMetrics
import concurrent.futures
import mplcyberpunk,re
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
font_all=('微软雅黑',14)
font_txt=('微软雅黑',11)
top_col='black'#顶部组件颜色
left_col='#2B2B2B'#左侧组件颜色
main_col='#242424'#中间组件颜色
button_hover_col='#0b3289'#鼠标放在按钮上的颜色
button_col='#0b3289'#按钮颜色
theme='dark'#light, dark, system
theme_col='dark-blue'#"blue", "green", "dark-blue", "sweetkind"
current_phone_serial=None
current_canvas = None
current_ani = None
current_file_path = os.path.dirname(os.path.abspath(sys.argv[0]))
# def get_screen_size():
#     """获取缩放后的分辨率"""
#     w = GetSystemMetrics (0)
#     h = GetSystemMetrics (1)
#     '''获取真实分辨率'''
#     # hDC = win32gui.GetDC(0)
#     # w = win32print.GetDeviceCaps(hDC, win32con.DESKTOPHORZRES)
#     # h = win32print.GetDeviceCaps(hDC, win32con.DESKTOPVERTRES)
  
#     return w,h
# w,h=get_screen_size()

current_phone_serial=None



def main():
    def get_connected_devices():
        result = adbCommandEx("adb.exe devices")
        output = result.split('\n')
        devices = [re.split(r'\s+', line)[0] for line in output[1:] if line.strip() != '']
        if devices:
            return devices
        else:
            return ['未连接设备']
    def adbCommandEx(command):#执行adb命令
        returnString = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE,
                                        stderr=subprocess.STDOUT).stdout.read().decode()
        return returnString.strip()
    def show_toast(message, duration=1000):#toast窗口
        toast = ctk.CTkToplevel(fg_color=main_col)
        toast.geometry(f"200x80+{w//2}+{h//2}")
        toast.overrideredirect(True)  # 隐藏标题栏和边框
        toast.attributes("-topmost", True)  # 窗口置顶
        label = ctk.CTkLabel(toast, text=message,font=('微软雅黑',20),fg_color='#14375E',text_color='white',corner_radius=10)
        label.place(relx=0, rely=0, relwidth=1, relheight=1)
        toast.after(duration, toast.destroy) 
    
    def restartadb():#重启adb
        close_matplotlib()
        adbCommandEx('adb.exe kill-server')
        adbCommandEx('adb.exe start-server')  
        ctkoptionmenu.configure(values=get_connected_devices())
        ctkoptionmenu.set(get_connected_devices()[0])
        show_toast('adb重启成功')
    def grep(result,str):#类似linux的grep指令
        for l in result.splitlines(True):
            if str in l:
                return l
    def morefunction(btn):#对应【更多功能】按钮
        close_matplotlib()
        if btn[5].winfo_ismapped():#判断btn5是否放置在窗口上，如果已放置就forget，显示前4个按钮
            for i,v in list(enumerate(btn)):
                if i<=4:
                    v.place(relx=0, rely=0.15+(0.14*i), relwidth=1, relheight=0.1)       
                else:
                    v.place_forget()#取消放置                
        else:
            for i,v in list(enumerate(btn)):
                if i>4:
                    v.place(relx=0, rely=0.15+0.14*(i-5), relwidth=1, relheight=0.1)
                else:
                    v.place_forget()
        
    
    def show_input_dialog(txt='输入：',initxt=''):#输入弹出窗口
        x=w//2
        y=h//2
        dialog = ctk.CTkInputDialog(text=txt,title='INPUT',ini_txt=initxt)
        dialog.geometry(f'+{x}+{y}')

        restr=dialog.get_input()
        return restr
                
    def PushAndPull(type):#设备文件导出和导入功能
        if type==1:
            file = ctk.filedialog.askopenfilename()
            filepath = os.path.abspath(file)
            if file :
                result=show_input_dialog('输入手机文件地址：')
                if result:
                    adbCommandEx(f'adb.exe -s {current_phone_serial} push {filepath} {result}')
                elif result=='':
                    adbCommandEx(f'adb.exe -s {current_phone_serial} push {filepath} /sdcard/')
               
        elif type==2:
            result=show_input_dialog('输入手机文件地址：')
            if result:
                file = ctk.filedialog.askdirectory()
                filepath = os.path.abspath(file)
                if file:
                    adbCommandEx(f'adb.exe -s {current_phone_serial} pull {result} {filepath}')
                
            elif result == '':
                result='/sdcard/Download/'
                file = ctk.filedialog.askdirectory()
                filepath = os.path.abspath(file)
                if file:
                    adbCommandEx(f'adb.exe -s {current_phone_serial} pull {result} {filepath}')
                   
    def getlogcat():#获取logcat日志
        # file_path='D:\logcat.txt'
        # adbCommandEx(f'adb.exe -s {current_phone_serial} logcat -d -v time *:E> {file_path}')  
        filepath = ctk.filedialog.asksaveasfilename(defaultextension=".txt", initialfile="logcat.txt", filetypes=[("Text files", "*.txt"), ("All files", "*.*")])
         
        if filepath:   
            adbCommandEx(f'adb.exe -s {current_phone_serial} logcat -d -v time *:E> {filepath}')  
            show_toast('logcat日志已导出')
    def close_matplotlib():
        global current_canvas, current_ani
        if current_canvas:
            current_ani.event_source.stop()  # 停止动画更新
            plt.close()  # 关闭matplotlib图形
            current_canvas.get_tk_widget().destroy()
            current_canvas, current_ani=None,None
    def devicemonitor(t):
        def action(selected_option):
            matplotpaint(t,selected_option)
        try:
            result=adbCommandEx(f'adb.exe -s {current_phone_serial} shell pm list packages -3').split('\n')
            packages=[pkg[8:] for pkg in result if pkg]
            listbox = CTkListbox(main_frame, command=action,justify='center')
            listbox.place(relx=0, rely=0, relwidth=0.989, relheight=1)
            for i in range(len(packages)):
                listbox.insert(i,packages[i])
        except:
            pass
    def matplotpaint(t,pname):
        for widget in main_frame.winfo_children():
            widget.destroy()
        adbCommandEx(f'adb.exe -s {current_phone_serial} shell monkey -p {pname} -c android.intent.category.LAUNCHER 1')
          # 销毁Tkinter中的绘图区域
        global current_canvas,current_ani
        matplotlib.use('TkAgg')
        plt.style.use('cyberpunk.mplstyle')
        plt.rcParams['font.sans-serif'] = ['SimHei']
        
        x_data = []
        y_data = []
        def getTotal():
            if t==1:
                result=grep(adbCommandEx(f'adb.exe -s {current_phone_serial} shell dumpsys meminfo {pname}'),'TOTAL')
                return result
            if t==2:
                result=grep(adbCommandEx(f'adb.exe -s {current_phone_serial} shell top -n 1'),pname)
                # result=grep(adbCommandEx(f'adb.exe -s {current_phone_serial} shell ps -f'),pname)
                return result
            else:
                return None
        def update_data(frame):
            info = getTotal()
            if info:
                if t == 1:
                    used_ram = float(info.splitlines()[0].strip().split()[1]) / 1024  # MB为单位
                elif t == 2:
                    cpu_usage = float(info.splitlines()[0].strip().split()[8])
                
                x_data.append(frame)
                y_data.append(used_ram if t == 1 else cpu_usage)  # 根据t更新y_data
                line.set_data(x_data, y_data)
                ax.relim()
                ax.autoscale_view()
                return line
    
        
        fig, ax = plt.subplots()
        line, = ax.plot(x_data, y_data)
        #解决中文乱码问题
        ax.set_xlabel('时间') 
        if t==1:
            ax.set_ylabel('内存占用 (MB)')  
        else:
            ax.set_ylabel('CPU占用 (%)')     
        current_ani = animation.FuncAnimation(fig, update_data, interval=100)
        current_canvas = FigureCanvasTkAgg(fig, master=main_frame)  # Tkinter中的绘图区域
        current_canvas.draw()
        current_canvas.get_tk_widget().pack(fill="both", expand=True)
       
    def localInstall(a=0):#安装apk
        file = ctk.filedialog.askopenfilename()
        filepath = os.path.abspath(file)
        if file != '':
            if a==0:
                adbCommandEx(f'adb.exe -s {current_phone_serial} install {filepath}')
                show_toast('安装成功')
            else:
                for d in get_connected_devices():
                    adbCommandEx(f'adb.exe -s {d} install {filepath}')
                    show_toast(f'设备{d}安装成功')    
    
        

    def wifiadb():#无线调试
        import socket
        hostname = socket.gethostname()
        ip_address = socket.gethostbyname(hostname).rsplit('.',maxsplit=1)[0]+'.'
        ip_port=''
        if getip()=="未连接网络":
            ip_port=show_input_dialog('输入IP地址及端口：',initxt=ip_address)#自动输入网段
        else:
            ip_port=show_input_dialog('输入IP地址及端口：',initxt=getip())
        if ip_port:
            adbCommandEx(f'adb.exe -s {current_phone_serial} connect {ip_port}')
        else:
            show_toast('未输入IP地址及端口')
    def showAuthor():
        adbversion=adbCommandEx('adb.exe version').splitlines(True)[0].rsplit(' ',1)[-1].strip()
        label=ctk.CTkLabel(main_frame,text=f'\n\n\n\n\n\n软件版本: V1.3.0\nADBversion:{adbversion}\n开发者:王亚飞\n\n\n\n\n\n\n',font=('微软雅黑',30),fg_color='#14375E',text_color='white',corner_radius=10)
        label.place(relx=0, rely=0, relwidth=1, relheight=1)
    def apkextract():#apk导出
        apkpath=adbCommandEx(f'adb.exe shell -s {current_phone_serial} pm path com.pantum.mobileprint').strip().split(':')[-1]
        adbCommandEx(f'adb.exe pull {apkpath} ./com.pantum.mobile.apk')
        show_toast('提取成功')
    def clustercast():
        screensize="2340"
        x,y=0,0
        for d in get_connected_devices():
            brand=adbCommandEx(f"adb.exe -s {d} shell getprop ro.product.brand").strip()
            subprocess.Popen(f'{current_file_path}\\scrcpy-win64-v2.5\\scrcpy.exe -s {d} --window-title={brand} -window-x={x} --window-y={y}')



    def getip():
        info=grep(adbCommandEx(f"adb.exe -s {current_phone_serial} shell ifconfig wlan0"),'inet ') 
        if info:
            ip=info.split(':')[1].split()[0].strip()
            return ip
        else:
            info=grep(adbCommandEx("adb.exe shell ip addr show wlan0"),"inet")
            if info:
                ip=info.split()[1].split("/")[0]
                return ip
            else:
                return "未连接网络"
    def button(cur_btn):
        
        for widget in main_frame.winfo_children():
            close_matplotlib()
    
            widget.destroy()
        if cur_btn==5:
            b1pic = ctk.CTkImage(light_image=Image.open('./imgs/connect.png'))
            b2pic = ctk.CTkImage(light_image=Image.open('./imgs/cont.png'))
            l1=ctk.CTkLabel(main_frame,text='打开手机无线adb开关,保证手机电脑同wifi,点击【连接】,输入IP地址和端口',font=font_all)
            b1=ctk.CTkButton(main_frame,text='连接',font=font_all,image=b1pic,text_color='white',fg_color=top_col,command=lambda: wifiadb())
            l1.pack(fill='x')
            b1.pack(fill='x')
            return 5
        try:
            if cur_btn==0:
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    # 提交任务给线程池，并获取 Future 对象
                    future1 = executor.submit(lambda: adbCommandEx(f"adb.exe -s {current_phone_serial} shell getprop ro.product.brand").strip())
                    future2 = executor.submit(lambda: adbCommandEx(f"adb.exe -s {current_phone_serial} shell getprop ro.build.version.release").strip())
                    future3 = executor.submit(lambda: grep(adbCommandEx(f"adb.exe -s {current_phone_serial} shell cat /proc/meminfo"),'MemTotal').split(':')[-1].strip())
                    future4 = executor.submit(lambda: adbCommandEx(f"adb.exe -s {current_phone_serial} shell wm size").split()[-1].strip())
                    future5 = executor.submit(lambda: adbCommandEx(f"adb.exe -s {current_phone_serial} shell wm density").split()[-1].strip())
                    future6 = executor.submit(lambda: grep(adbCommandEx(f"adb.exe -s {current_phone_serial} shell dumpsys battery"),'level').split(':')[-1].strip())
                    future7 = executor.submit(lambda: getip())
                    future8 = executor.submit(lambda: adbCommandEx(f"adb.exe -s {current_phone_serial} shell df -h sdcard").split()[-5].strip())
                    future9 = executor.submit(lambda: adbCommandEx(f"adb.exe -s {current_phone_serial} shell dumpsys window | findstr mCurrentFocus").strip().split()[-1].split('}')[0])
                
                    brand = future1.result()
                    version = future2.result()
                    mem = future3.result()
                    size=future4.result()
                    pixel=future5.result()
                    battery=future6.result()
                    ip=future7.result()
                    storage=future8.result()
                    packname=future9.result()
                
                textc=f'\n\n\n\n品牌：{brand}\nAndroid版本：{version}\n内存大小：{mem}\n分辨率：{size}\n像素密度：{pixel} dpi\n本机IP：{ip}\n当前电量：{battery}%\n存储：{storage}\n当前运行包名：{packname}'
                text=ctk.CTkTextbox(main_frame,font=('微软雅黑',20),fg_color=main_col,bg_color='white',corner_radius=0)
                text.tag_config("center", justify="center")
                text.place(relx=0, rely=0, relwidth=1, relheight=1.01)
                text.insert('0.0',textc,'center')
                text.configure(state="disabled")
            
            elif cur_btn==1:
                b1pic = ctk.CTkImage(light_image=Image.open('./imgs/unlock.png'))
                b1=ctk.CTkButton(main_frame,text='解锁',font=font_all,text_color='white',image=b1pic,fg_color=top_col,command=lambda: adbCommandEx(f'adb.exe -s {current_phone_serial} shell input keyevent  82'))
                b2pic = ctk.CTkImage(light_image=Image.open('./imgs/back.png'))
                b2=ctk.CTkButton(main_frame,text='返回',font=font_all,text_color='white',image=b2pic,fg_color=top_col,command=lambda: adbCommandEx(f'adb.exe -s {current_phone_serial} shell input keyevent  4'))
                b3pic = ctk.CTkImage(light_image=Image.open('./imgs/restart.png'))
                b3=ctk.CTkButton(main_frame,text='重启',font=font_all,text_color='white',image=b3pic,fg_color=top_col,command=lambda: adbCommandEx(f'adb.exe -s {current_phone_serial} shell reboot'))
                imgname=time()
                b4pic = ctk.CTkImage(light_image=Image.open('./imgs/screenshot.png'))
                b4=ctk.CTkButton(main_frame,text='截图',font=font_all,text_color='white',image=b4pic,fg_color=top_col,command=lambda: adbCommandEx(f'adb.exe -s {current_phone_serial} shell screencap -p /sdcard/Download/{imgname}.png'))
                b5=ctk.CTkButton(main_frame,text='启动奔图',font=font_all,text_color='white',fg_color=top_col,command=lambda: adbCommandEx(f'adb.exe -s {current_phone_serial} shell am start com.pantum.mobileprint/.login.activity.welcome.WelcomeActivity'))
                b6=ctk.CTkButton(main_frame,text='关闭奔图',font=font_all,text_color='white',fg_color=top_col,command=lambda: adbCommandEx(f'adb.exe -s {current_phone_serial} shell am force-stop com.pantum.mobileprint'))
                b7pic = ctk.CTkImage(light_image=Image.open('./imgs/power.png'))
                b7=ctk.CTkButton(main_frame,text='电源',font=font_all,text_color='white',image=b7pic,fg_color=top_col,command=lambda: adbCommandEx(f'adb.exe -s {current_phone_serial} shell input keyevent 26'))
                b8pic = ctk.CTkImage(light_image=Image.open('./imgs/install.png'))
                b8=ctk.CTkButton(main_frame,text='安装应用',font=font_all,text_color='white',image=b8pic,fg_color=top_col,command=lambda: localInstall())
                b9pic = ctk.CTkImage(light_image=Image.open('./imgs/copy.png'))
                b9=ctk.CTkButton(main_frame,text='提取apk',font=font_all,text_color='white',image=b9pic,fg_color=top_col,command=lambda: apkextract())
                b10pic = ctk.CTkImage(light_image=Image.open('./imgs/adbshell.png'))
                b10=ctk.CTkButton(main_frame,text='adb shell',font=font_all,text_color='white',image=b10pic,fg_color=top_col,command=lambda: os.system("start cmd /k adb.exe shell"))
                b11pic = ctk.CTkImage(light_image=Image.open('./imgs/cast.png'))
                current_file_path = os.path.abspath(__file__).rsplit('\\',maxsplit=1)[0]
                brand=adbCommandEx(f"adb.exe -s {current_phone_serial} shell getprop ro.product.brand").strip()
                b11=ctk.CTkButton(main_frame,text='投屏控制',font=font_all,text_color='white',image=b11pic,fg_color=top_col,command=lambda: subprocess.Popen([f"{current_file_path}\\scrcpy-win64-v2.5\\scrcpy.exe", f'--window-title={brand}', "-s", current_phone_serial]))
                b1.pack(fill='x')
                b2.pack(fill='x')
                b3.pack(fill='x')
                b4.pack(fill='x')
                b5.pack(fill='x')
                b6.pack(fill='x')
                b7.pack(fill='x')
                b8.pack(fill='x')
                b9.pack(fill='x')
                b10.pack(fill='x')
                b11.pack(fill='x')
            elif cur_btn==2:
                b1pic = ctk.CTkImage(light_image=Image.open('./imgs/out.png'))
                b1=ctk.CTkButton(main_frame,text='导出logcat日志',font=font_all,text_color='white',image=b1pic,fg_color=top_col,command=lambda: getlogcat())
                b2pic = ctk.CTkImage(light_image=Image.open('./imgs/clear.png'))
                b2=ctk.CTkButton(main_frame,text='清除logcat日志',font=font_all,text_color='white',image=b2pic,fg_color=top_col,command=lambda: adbCommandEx(f'adb.exe -s {current_phone_serial} logcat -c'))
                b3pic = ctk.CTkImage(light_image=Image.open('./imgs/real.png'))
                b3=ctk.CTkButton(main_frame,text='实时logcat监控',font=font_all,text_color='white',image=b3pic,fg_color=top_col,command=lambda: os.system(f"start cmd /k adb.exe -s {current_phone_serial} logcat"))
                b1.pack(fill='x')
                b2.pack(fill='x')
                b3.pack(fill='x')
                
            elif cur_btn==3:
                b1pic = ctk.CTkImage(light_image=Image.open('./imgs/memmonitor.png'))
                b1=ctk.CTkButton(main_frame,text='内存监控',font=font_all,image=b1pic,text_color='white',fg_color=top_col,command=lambda: devicemonitor(1))
                b2pic = ctk.CTkImage(light_image=Image.open('./imgs/cpu.png'))
                b2=ctk.CTkButton(main_frame,text=' cpu监控',font=font_all,image=b2pic,text_color='white',fg_color=top_col,command=lambda: devicemonitor(2))
                b1.pack(fill='x')
                b2.pack(fill='x')
            elif cur_btn==4:
                b1pic = ctk.CTkImage(light_image=Image.open('./imgs/upload.png'))
                b2pic = ctk.CTkImage(light_image=Image.open('./imgs/download.png'))
                b1=ctk.CTkButton(main_frame,text='上传至手机',font=font_all,image=b1pic,text_color='white',fg_color=top_col,command=lambda: PushAndPull(1))
                b2=ctk.CTkButton(main_frame,text='下载至电脑',font=font_all,image=b2pic,text_color='white',fg_color=top_col,command=lambda: PushAndPull(2))
                b3=ctk.CTkButton(main_frame,text='文件管理',font=font_all,text_color='white',fg_color=top_col,command=lambda: os.system("start filepilot.exe"))
                b1.pack(fill='x')
                b2.pack(fill='x')
                b3.pack(fill='x')
            
            elif cur_btn==6:
                def adbCommand(command, spestr=''):
                    returnString=adbCommandEx(command)
                    txt.insert('0.0', f'{spestr}{returnString}\n')
                def getApkPackageName():
                    file = ctk.filedialog.askopenfilename()
                    filepath = os.path.abspath(file)
                    if file != '':
                        command = f'aapt dump badging {filepath} | findstr package'
                        adbCommand(command,'文件包名：')
                    else:
                        txt.insert('0.0', '未选择文件\n')

                win = ctk.CTkToplevel()
                ctk.set_appearance_mode('dark')
                ctk.set_default_color_theme('dark-blue')
                x=(w-860)//2
                y=(h-560)//2
            
                win.geometry(f'860x560+{x}+{y}')
                win.title('adbtool')
                txtframe=ctk.CTkFrame(win)
                txtframe.place(relx=0,rely=0.3, relheight=0.7, relwidth=1)
                scrollbar = ctk.CTkScrollbar(txtframe)
                def current_line_excute():
                    line_start = txt.index("insert linestart")
                    line_end = txt.index("insert lineend")
                    current_line_chars = txt.get(line_start, line_end).strip()
                    adbCommand(current_line_chars)
                txt = ctk.CTkTextbox(txtframe,font=font_all)
                txt.place(relx=0,rely=0, relheight=1, relwidth=1)
                txt.bind('<Return>',lambda event: current_line_excute())
                scrollbar.pack(side=ctk.RIGHT,fill=ctk.Y)
                btn1 = ctk.CTkButton(win, text='获取设备',
                                    command=lambda: adbCommand('adb.exe devices','设备列表：\n'),font=font_all,corner_radius=0)
                btn1.place(relx=0, rely=0, relwidth=0.2,relheight=0.1)
                btn2 = ctk.CTkButton(win, text='查看安装包名', 
                                    command=lambda: adbCommand(f'adb.exe -s {current_phone_serial} shell pm list packages','设备包名：\n'),font=font_all,corner_radius=0)
                btn2.place(relx=0, rely=0.1, relwidth=0.2, relheight=0.1)
                btn3 = ctk.CTkButton(win, text='查看第三方包名', 
                                    command=lambda: adbCommand(f'adb.exe -s {current_phone_serial} shell pm list packages -3','设备第三方包名\n'),font=font_all,corner_radius=0)
                btn3.place(relx=0, rely=0.2, relwidth=0.2, relheight=0.1)
                btn4 = ctk.CTkButton(win, text='获取本地包名',
                                    command=getApkPackageName,font=font_all,corner_radius=0)
                btn4.place(relx=0.2, rely=0, relwidth=0.2, relheight=0.1)
                btn5 = ctk.CTkButton(win, text='cpu信息', command=lambda: adbCommand(f'adb.exe -s {current_phone_serial} shell cat /proc/cpuinfo','cpu信息：\n'),font=font_all,corner_radius=0)
                btn5.place(relx=0.2, rely=0.1, relwidth=0.2, relheight=0.1)
                btn6 = ctk.CTkButton(win, text='内存信息',command=lambda: adbCommand(f'adb.exe -s {current_phone_serial} shell cat /proc/meminfo','内存信息：\n'),font=font_all,corner_radius=0)
                btn6.place(relx=0.2, rely=0.2, relwidth=0.2, relheight=0.1)
                btn7 = ctk.CTkButton(win, text='手机及系统属性', command=lambda:adbCommand(f'adb.exe -s {current_phone_serial} shell cat /system/build.prop','设备属性：\n'),font=font_all,corner_radius=0)
                btn7.place(relx=0.4, rely=0, relwidth=0.2, relheight=0.1)
                win.focus_set()
                win.grab_set()
                
            elif cur_btn==8:
                b1pic = ctk.CTkImage(light_image=Image.open('./imgs/unlock.png'))
                b1=ctk.CTkButton(main_frame,text='解锁',font=font_all,text_color='white',image=b1pic,fg_color=top_col,command=lambda: [adbCommandEx(f'adb.exe -s {d} shell input keyevent  82') for d in get_connected_devices() ])
                b2pic = ctk.CTkImage(light_image=Image.open('./imgs/back.png'))
                b2=ctk.CTkButton(main_frame,text='返回',font=font_all,text_color='white',image=b2pic,fg_color=top_col,command=lambda: [adbCommandEx(f'adb.exe -s {d} shell input keyevent  4') for d in get_connected_devices() ])
                b3pic = ctk.CTkImage(light_image=Image.open('./imgs/restart.png'))
                b3=ctk.CTkButton(main_frame,text='重启',font=font_all,text_color='white',image=b3pic,fg_color=top_col,command=lambda: [adbCommandEx(f'adb.exe -s {d} reboot') for d in get_connected_devices() ])
                imgname=time()
                b4pic = ctk.CTkImage(light_image=Image.open('./imgs/screenshot.png'))
                b4=ctk.CTkButton(main_frame,text='截图',font=font_all,text_color='white',image=b4pic,fg_color=top_col,command=lambda: [adbCommandEx(f'adb.exe -s {d} shell screencap -p /sdcard/Download/{imgname}.png') for d in get_connected_devices() ])
                b5=ctk.CTkButton(main_frame,text='启动奔图',font=font_all,text_color='white',fg_color=top_col,command=lambda: [adbCommandEx(f'adb.exe -s {d} shell am start com.pantum.mobileprint/.login.activity.welcome.WelcomeActivity') for d in get_connected_devices() ])
                b6=ctk.CTkButton(main_frame,text='关闭奔图',font=font_all,text_color='white',fg_color=top_col,command=lambda: [adbCommandEx(f'adb.exe -s {d} shell am force-stop com.pantum.mobileprint') for d in get_connected_devices() ])
                b7pic = ctk.CTkImage(light_image=Image.open('./imgs/power.png'))
                b7=ctk.CTkButton(main_frame,text='电源',font=font_all,text_color='white',image=b7pic,fg_color=top_col,command=lambda: [adbCommandEx(f'adb.exe -s {d} shell input keyevent 26') for d in get_connected_devices() ])
                b8pic = ctk.CTkImage(light_image=Image.open('./imgs/install.png'))
                b8=ctk.CTkButton(main_frame,text='安装应用',font=font_all,text_color='white',image=b8pic,fg_color=top_col,command=lambda: localInstall(1))
                b9pic = ctk.CTkImage(light_image=Image.open('./imgs/cast.png'))
                b9=ctk.CTkButton(main_frame,text='投屏控制',font=font_all,text_color='white',image=b9pic,fg_color=top_col,command=lambda: clustercast())
                b1.pack(fill='x')
                b2.pack(fill='x')
                b3.pack(fill='x')
                b4.pack(fill='x')
                b5.pack(fill='x')
                b6.pack(fill='x')
                b7.pack(fill='x')
                b8.pack(fill='x')
                b9.pack(fill='x')
        except AttributeError :
            show_toast('未连接设备')
        
    ctk.set_appearance_mode(theme)#light, dark, system
    ctk.set_default_color_theme(theme_col)#"blue", "green", "dark-blue", "sweetkind"
    
    #绘制主窗口
    app = ctk.CTk()
    w = app.winfo_screenwidth()
    h = app.winfo_screenheight()
    x=(w-860)//2
    y=(h-560)//2
    #窗口位置
    app.geometry(f'860x560+{x}+{y}')
    app.title("adbtools")#窗口标题
    app.overrideredirect(True)#窗口无边框
    # app.attributes('-topmost', True)#窗口置顶
    # app.lift()
    app.attributes('-toolwindow', True)
    def start_move(event):
        global x_offset, y_offset
        x_offset = event.x
        y_offset = event.y
    def stop_move(event):
        global x_offset, y_offset
        x_offset = None
        y_offset = None
    
    def on_drag(event):
        global x_offset, y_offset
        if x_offset is not None and y_offset is not None:
            app.geometry(f"+{event.x_root - x_offset}+{event.y_root - y_offset}")
    top_frame=ctk.CTkFrame(app,fg_color=top_col)#标题栏
    top_frame.place(relx=0, rely=0, relwidth=1, relheight=0.08)
    top_frame.bind('<Button-1>', start_move)#标题栏拖动效果
    top_frame.bind('<B1-Motion>', on_drag)
    top_frame.bind('<ButtonRelease-1>', stop_move)
        
    left_frame=ctk.CTkFrame(app,fg_color=left_col)
    left_frame.place(relx=0, rely=0.08, relwidth=0.08, relheight=0.92)
    
    main_frame = ctk.CTkFrame(app,fg_color=main_col)
    main_frame.place(relx=0.08, rely=0.08, relwidth=0.93, relheight=0.92)
    pic00 =  ctk.CTkImage(light_image=Image.open('./imgs/more.png'))
    more = ctk.CTkButton (top_frame,text='',font=font_all,fg_color=top_col,image=pic00,hover_color=button_hover_col,command=lambda: morefunction(btn_list))
    more.place(relx=0, rely=0, relwidth=0.08, relheight=1)
    
    pic01 =  ctk.CTkImage(light_image=Image.open('./imgs/restart.png'))
    restart = ctk.CTkButton (top_frame,text='',font=font_all,fg_color=top_col,image=pic01,hover_color=button_hover_col,command=lambda: restartadb())
    restart.place(relx=0.08, rely=0, relwidth=0.08, relheight=1)
 

    def update_option_menu():
        devices = get_connected_devices()        
        ctkoptionmenu.configure(values=devices)
        t=ctkoptionmenu.get()
        if t not in devices:
            ctkoptionmenu.set(devices[0])
            link_current_phone(devices[0])
        app.after(1000, update_option_menu) # 每隔5秒更新一次OptionMenu
    def link_current_phone(choice):
        global current_phone_serial
        current_phone_serial=choice


    global current_phone_serial
    current_phone_serial=get_connected_devices()[0]
    ctkoptionmenu=ctk.CTkOptionMenu(top_frame,values=get_connected_devices(),dynamic_resizing=True,anchor="center",button_hover_color='#14375E',fg_color='#14375E',command=link_current_phone)
    ctkoptionmenu.place(relx=0.16, rely=0, relwidth=0.15, relheight=1)
    update_option_menu()
    #电量
    # batterybar = ctk.CTkProgressBar(top_frame, orientation="horizontal",corner_radius=5,progress_color=button_col)
    # batterybar.set(value=float("0."+grep(adbCommandEx(f"adb.exe -s {current_phone_serial} shell dumpsys battery"),'level').split(':')[-1].strip()))
    # batterybar.place(relx=0.66, rely=0.35, relwidth=0.03, relheight=0.3)
    
    pic02 = ctk.CTkImage(light_image=Image.open('./imgs/exit.png'))
    exit = ctk.CTkButton (top_frame,text='',font=font_all,fg_color=top_col,image=pic02,hover_color="red",command=app.quit)
    exit.place(relx=0.95, rely=0, relwidth=0.05, relheight=1)
    
    def on_closing():
        close_matplotlib()
        app.destroy()
    
    app.bind("<Escape>", lambda event: app.quit())
    app.protocol("WM_DELETE_WINDOW", on_closing)
    
    
    pic0 = ctk.CTkImage(light_image=Image.open('./imgs/info.png'))
    btn0 = ctk.CTkButton(left_frame, text='',font=font_all,fg_color=left_col,hover_color=button_hover_col,image=pic0,command=lambda: button(0))
    pic1 = ctk.CTkImage(light_image=Image.open('./imgs/control.png'))
    btn1 = ctk.CTkButton(left_frame, text='',font=font_all,fg_color=left_col,hover_color=button_hover_col,image=pic1,command=lambda: button(1))
    pic2 = ctk.CTkImage(light_image=Image.open('./imgs/log.png'))
    btn2 = ctk.CTkButton(left_frame, text='',font=font_all,fg_color=left_col,hover_color=button_hover_col,image=pic2,command=lambda: button(2))
    pic3 = ctk.CTkImage(light_image=Image.open('./imgs/monitor.png'))
    btn3 = ctk.CTkButton(left_frame, text='',font=font_all,fg_color=left_col,hover_color=button_hover_col,image=pic3,command=lambda: button(3))
    pic4 = ctk.CTkImage(light_image=Image.open('./imgs/trans.png'))
    btn4 = ctk.CTkButton(left_frame, text='',font=font_all,fg_color=left_col,hover_color=button_hover_col,image=pic4,command=lambda: button(4))
    pic5 = ctk.CTkImage(light_image=Image.open('./imgs/remote.png'))
    btn5 = ctk.CTkButton(left_frame, text='',font=font_all,fg_color=left_col,hover_color=button_hover_col,image=pic5,command=lambda: button(5))
    pic6 = ctk.CTkImage(light_image=Image.open('./imgs/toolbox.png'))
    btn6 = ctk.CTkButton(left_frame, text='',font=font_all,fg_color=left_col,hover_color=button_hover_col,image=pic6,command=lambda: button(6))
    pic7 = ctk.CTkImage(light_image=Image.open('./imgs/cmd.png'))
    btn7 = ctk.CTkButton(left_frame, text='',font=font_all,fg_color=left_col,hover_color=button_hover_col,image=pic7,command=lambda: os.system("start cmd"))
    pic8 = ctk.CTkImage(light_image=Image.open('./imgs/cluster.png'))
    btn8 = ctk.CTkButton(left_frame, text='',font=font_all,fg_color=left_col,hover_color=button_hover_col,image=pic8,command=lambda: button(8))
    pic9 = ctk.CTkImage(light_image=Image.open('./imgs/warning.png'))
    btn9 = ctk.CTkButton(left_frame, text='',font=font_all,fg_color=left_col,hover_color=button_hover_col,image=pic9,command=lambda: showAuthor())
    t0=CTkToolTip(btn0, message="设备信息")
    t1=CTkToolTip(btn1, message="设备控制")
    t2=CTkToolTip(btn2, message="日志管理")
    t3=CTkToolTip(btn3, message="性能监控")
    t4=CTkToolTip(btn4, message="文件传输")
    t5=CTkToolTip(btn5, message="远程调试")
    t6=CTkToolTip(btn6, message="测试工具")
    t7=CTkToolTip(btn7, message="调试窗口")
    t8=CTkToolTip(btn8, message="集群控制")
    t9=CTkToolTip(btn9, message="关于软件")
    t_more=CTkToolTip(more, message="更多功能")
    t_re=CTkToolTip(restart, message="重启ADB")
    
    btn_list=[btn0,btn1,btn2,btn3,btn4,btn5,btn6,btn7,btn8,btn9]
    for i,v in list(enumerate(btn_list)):
            if i<=4:
                v.place(relx=0, rely=0.15+(0.14*i), relwidth=1, relheight=0.1)
                
    app.mainloop()
if __name__ == "__main__":  
    main()
 


