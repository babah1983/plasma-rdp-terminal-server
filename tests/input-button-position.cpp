// Exercise real KRdp input translation: a button PDU can be the first pointer PDU.
#include <QCoreApplication>
#include <QMouseEvent>
#include <QObject>
#include <memory>
#include <vector>
#include <cstdio>
#define private public
#include "InputHandler.h"
#undef private

int main(int argc, char **argv)
{
    QCoreApplication app(argc, argv);
    KRdp::InputHandler handler(nullptr);
    std::vector<std::shared_ptr<QInputEvent>> events;
    QObject::connect(&handler, &KRdp::InputHandler::inputEvent, &app, [&](auto event) { events.push_back(event); });
    auto check = [&](QPointF position, QEvent::Type type, Qt::MouseButton button) {
        if (events.size() != 2 || events[0]->type() != QEvent::MouseMove || events[1]->type() != type)
            return false;
        auto move = std::static_pointer_cast<QMouseEvent>(events[0]);
        auto click = std::static_pointer_cast<QMouseEvent>(events[1]);
        return move->position() == position && click->position() == position && click->button() == button;
    };
    handler.mouseEvent(780, 270, PTR_FLAGS_BUTTON1 | PTR_FLAGS_DOWN);
    bool press = check({780, 270}, QEvent::MouseButtonPress, Qt::LeftButton);
    events.clear();
    handler.mouseEvent(0, 0, PTR_FLAGS_BUTTON1);
    bool release = check({0, 0}, QEvent::MouseButtonRelease, Qt::LeftButton);
    events.clear();
    handler.extendedMouseEvent(210, 310, PTR_XFLAGS_BUTTON1 | PTR_XFLAGS_DOWN);
    bool extended = check({210, 310}, QEvent::MouseButtonPress, Qt::BackButton);
    events.clear();
    handler.mouseEvent(500, 600, PTR_FLAGS_MOVE);
    bool motion = events.size() == 1 && events[0]->type() == QEvent::MouseMove;
    std::printf("button_position_press=%d release_at_origin=%d extended=%d motion=%d\n", press, release, extended, motion);
    return press && release && extended && motion ? 0 : 1;
}
