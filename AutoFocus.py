import numpy as np
import cv2
import pigpio
import time 



class Camera():
    def __init__(self,port=0,servo_pin=18):
        self.port=port
        self.start_x,self.start_y,self.end_x,self.end_y=-1,-1,-1,-1
        self.prew_start_x,self.prew_start_y,self.prew_end_x,self.prew_end_y=-1,-1,-1,-1
        self.servo_pin=servo_pin
        self.pi=pigpio.pi()
        self.pi.set_mode(servo_pin,pigpio.OUTPUT)
        self.max_focus_delentropy=0
        self.max_focus_laplacian=0
        self.focus_list_delentropy=list()
        self.focus_list_laplacian=list()
        self.done=False
        self.angle=0
        self.imagelist=[]
        self.first=True
        time.sleep(1)
    def begin(self):
        self.cap=cv2.VideoCapture(self.port)
        if not self.cap.isOpened():
            print("Camera can not opened")
            return
        cv2.namedWindow("Camera")
        cv2.setMouseCallback("Camera",self.click_and_release_focus)

    def set_angle(self,angle):
        pulse_width=int((angle/180)*(2500-500)+500)
        self.pi.set_servo_pulsewidth(self.servo_pin,pulse_width)
        time.sleep(1)

    def start_focus(self):
        while True:
            self.ret,self.frame=self.cap.read()
           
            if self.ret:
                if self.start_x!=-1 and self.start_y!=-1 and self.end_x!=-1 and self.end_y!=-1:
                    self.cropped_image=self.crop_image(self.frame)
                    if self.start_x!=self.prew_start_x or self.start_y!=self.prew_start_y or self.end_x!=self.prew_end_x or self.end_y!= self.prew_end_y: 
                        self.prew_start_x=self.start_x
                        self.prew_start_y=self.start_y
                        self.prew_end_x=self.end_x
                        self.prew_end_y=self.end_y
                        self.maxpos=135
                        self.minpos=0
                        self.counter=10
                        self.imagelist=[]
                        self.focus_list_delentropy=[]
                        self.focus_list_laplacian=[]
                        self.first=True
                        while True:
                            if(self.angle<=0):
                                self.angle=0
                                break
                            self.angle-=10
                        self.done=False
                    
                    if self.done==True:
                        pass
                    elif(self.angle>=self.maxpos):
                        self.max_focus_delentropy=max(self.focus_list_delentropy)
                        self.max_focus_laplacian=max(self.focus_list_laplacian)
                        cv2.imwrite("Çıktı.jpg",self.imagelist[self.focus_list_delentropy.index(self.max_focus_delentropy)])
                        self.done=True
                        
                    else:
                        self.set_angle(self.angle)
                        time.sleep(1)
                        self.gray=cv2.cvtColor(self.cropped_image,cv2.COLOR_BGR2GRAY)
                        self.laplacian=self.detect_focus_laplacian(self.gray)
                        self.delentropy=self.detect_focus_delentropy(self.gray)
                        if (self.first!=True):
                            self.imagelist.append(self.frame)
                            self.focus_list_delentropy.append(self.delentropy)
                            self.focus_list_laplacian.append(self.laplacian)
                        if self.first:
                            self.first=False
                        time.sleep(1)
                        print("Laplacian",self.laplacian)
                        print("Entropy",self.delentropy)
                        self.angle+=self.counter 
                cv2.imshow("Camera",self.frame)
            if cv2.waitKey(1) & 0xFF==ord('q'):
                break
        self.cap.release()
        cv2.destroyAllWindows()
    def click_and_release_focus(self,event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            self.start_x,self.start_y = x, y
            self.end_x, self.end_y = x, y
        elif event == cv2.EVENT_LBUTTONUP:
    	    self.end_x,self.end_y = x, y
    
    def crop_image(self,frame):
        if (abs(self.end_x-self.start_x)<20 or abs(self.end_y-self.start_y)<20):
            cv2.rectangle(frame,(self.end_x-20,self.end_y-20),(self.end_x+20,self.end_y+20),(0,255,0),2)
            cropped_frame = frame[self.end_y-20:self.end_y+20,self.end_x-20:self.end_x+20]
        else:
            cv2.rectangle(frame,(self.start_x,self.start_y),(self.end_x,self.end_y),(0,255,0),2)
            if(self.start_y>self.end_y and self.start_x>self.end_x):
                cropped_frame=frame[self.end_y:self.start_y,self.end_x:self.start_x]
            elif(self.start_y>self.end_y):
                cropped_frame=frame[self.end_y:self.start_y,self.start_x:self.end_x]
            elif(self.start_x>self.end_x):
                cropped_frame=frame[self.start_y:self.end_y,self.end_x:self.start_x]
            else:
                cropped_frame = frame[self.start_y:self.end_y, self.start_x:self.end_x]
        return cropped_frame
    def detect_focus_laplacian(self,frame):
        laplacian=cv2.Laplacian(self.gray,cv2.CV_64F)
        variance=laplacian.var()
        return variance
    def detect_focus_delentropy(self,greyimg):
        # $\nabla f(n) \approx f(n) - f(n - 1)$
        fx = greyimg[:, 2:] - greyimg[:, :-2]
        fy = greyimg[2:, :] - greyimg[:-2, :]
        # fix shape
        fx = fx[1:-1, :]
        fy = fy[:, 1:-1]

        grad = fx + fy

        # ensure $-255 \leq J \leq 255$
        #jrng = np.max([np.max(np.abs(fx)), np.max(np.abs(fy))])
        #assert jrng <= 255, "J must be in range [-255, 255]"

        ### 1609.01117 page 16, eq 17

        hist, _, _ = np.histogram2d(fx.flatten(),fy.flatten(),bins=256,)

        ### 1609.01117 page 20, eq 22

        deldensity = hist / np.sum(hist)
        deldensity = deldensity * -np.ma.log2(deldensity)
        entropy = np.sum(deldensity)

        entropy /= 2  # 4.3 Papoulis generalized sampling halves the delentropy
        
        #print(f"entropy: {entropy}",f"entropy ratio: {entropy / 8.0}",)

        # the reference image seems to be bitwise inverted, I don't know why.
        # the entropy doesn't change when inverted, so both are okay in
        # the previous computational steps.
        param_invert = True

        #gradimg = np.invert(grad) if param_invert else grad

        return (entropy)




camera=Camera()
camera.begin()
camera.start_focus()
