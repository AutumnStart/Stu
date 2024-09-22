#include <iostream>
#include <opencv2/opencv.hpp>//引用头文件

using namespace std;
using namespace cv;//命名空间

int main(int argc, char *argv[])
{
//   读取
   Mat back =imread("C:/Qt/img/demo.png");
   Mat img=imread("C:/Qt/img/demo1.png");

   imshow("back",back);
   imshow("img",img);


//    图片转Hsv格式
    Mat hsv;
    cvtColor(img,hsv,COLOR_BGR2HSV);
    imshow("hsv",hsv);

//    识别颜色区域
    Mat mask,mask1;
    inRange(hsv,Scalar(156,120,120),Scalar(170,170,190),mask);
    imshow("mask",mask);

//    取反
    Mat umask;
    bitwise_not(mask,umask);
    imshow("umask",umask);

    //现在背景图片
    Mat bkmask;
    bitwise_and(back,back,bkmask,mask);
    imshow("bkmask",bkmask);
    Mat bkUmask;
    bitwise_and(img,img,bkUmask,umask);
    imshow("bkUmask",bkUmask);

    //像素融合
    Mat final;
    final=bkmask+bkUmask;
    imshow("final",final);


//    waitKey(0);
    Mat frame;
    VideoCapture capture(0);//参数为0时，表示调用默认摄像头
    while(capture.read(frame)){
        imshow("video",frame);
        waitKey(30);
    }

    return 0;//正常退出
}

