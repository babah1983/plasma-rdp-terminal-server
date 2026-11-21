// Exercise the production gate at the two lost-notification boundaries.
#include "producerwakeup_p.h"
#include <atomic>
#include <cstdio>
#include <future>
#include <thread>
#include <unistd.h>

int main()
{
    // A broken gate must fail the test instead of hanging the build indefinitely.
    alarm(15);
    PipeWireProducerWakeup work;
    work.notify();
    if (!work.wait()) return 1;
    work.notify(); // Producer signals while the consumer is processing a frame.
    if (!work.wait()) return 2;
    work.close();
    work.notify(); // Late work must never resurrect a closed producer.
    if (work.wait()) return 3;

    PipeWireProducerWakeup earlyStop;
    earlyStop.close(); // destroy() wins the race against worker startup.
    if (earlyStop.wait()) return 4;

    for (int i = 0; i < 1000; ++i) {
        PipeWireProducerWakeup encode, output;
        std::promise<void> entered;
        auto ready = entered.get_future();
        std::atomic_int stopped = 0;
        std::thread first([&] {
            entered.set_value();
            while (encode.wait()) output.notify();
            ++stopped;
        });
        std::thread second([&] {
            while (output.wait()) {}
            ++stopped;
        });
        ready.wait(); // Stop may land before or during the worker's wait.
        encode.notify();
        if (i % 2) std::this_thread::yield();
        encode.close();
        first.join();
        output.close();
        second.join();
        if (stopped != 2) return 5;
    }
    alarm(0);
    std::puts("producer_wakeup: queued work, early stop, late work, 1000 two-worker shutdowns passed");
}
