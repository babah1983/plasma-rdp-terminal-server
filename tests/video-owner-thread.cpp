// Exercise real KRdp callbacks with worker invocation, without opening a socket.
#include <QCoreApplication>
#include <QThread>
#include <QEvent>
#include <memory>
#include <thread>
#include <cstdio>
#include <QObject>
#define private public
#include "RdpConnection.h"
#undef private
#include "VideoStream.h"
int main(int argc,char **argv) {
    QCoreApplication app(argc,argv);
    KRdp::RdpConnection c(nullptr,-1);
    QCoreApplication::removePostedEvents(&c,QEvent::MetaCall); // Don't open the intentionally invalid test socket.
    auto stream=c.videoStream();
    QThread *enableThread=nullptr,*closeThread=nullptr;
    QObject::connect(stream,&KRdp::VideoStream::enabledChanged,&app,[&]{enableThread=QThread::currentThread();},Qt::DirectConnection);
    QObject::connect(stream,&KRdp::VideoStream::closed,&app,[&]{closeThread=QThread::currentThread();},Qt::DirectConnection);
    std::thread enable([&]{c.onSuppressOutput(1);});enable.join();
    QCoreApplication::sendPostedEvents(stream,QEvent::MetaCall);
    const bool enabled=stream->enabled()&&enableThread==stream->thread();
    std::thread close([&]{c.onClose();});close.join();
    QCoreApplication::sendPostedEvents(stream,QEvent::MetaCall);
    const bool closed=closeThread==stream->thread();
    std::printf("suppress_output_owner_thread=%d close_owner_thread=%d\n",enabled,closed);
    return enabled&&closed?0:1;
}
