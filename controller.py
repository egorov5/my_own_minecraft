from direct.showbase.ShowBase import ShowBase
from panda3d.core import CollisionTraverser, CollisionHandlerQueue
from panda3d.core import CollisionNode, CollisionSphere, BitMask32

# Класс контроллера мышки и клавиатуры
class Controller():
    # Конструктор
    def __init__(self):
        self.g = 0.015
        self.fallspeed = 0
        self.ground = False
        self.jump = 0.3

        self.edit_mode = True
        # значение шага перемещения клавиатурой
        self.key_step = 0.2
        # значение шага поворота мышкой
        self.mouse_step = 0.2

        # координаты центра экрана
        self.x_center = base.win.getXSize()//2
        self.y_center = base.win.getYSize()//2
        # перемещаем указатель мышки в центр экрана
        base.win.movePointer(0, self.x_center, self.y_center)
        # отключаем стандартное управление мышкой
        base.disableMouse()
        # устанавливаем поле зрения объектива
        base.camLens.setFov(80)
        # устанавливаем ближайшую границу отрисовки
        base.camLens.setNear(0.2)

        # устанавливаем текущие значения ориентации камеры
        self.heading = 0
        self.pitch = 0

        # запускаем задачу контроля камеры
        taskMgr.doMethodLater(0.02, self.controlCamera, "camera-task")
        # регистрируем на нажатие клавиши "Esc"
        # событие закрытия приложения
        base.accept("escape", base.userExit)

        # устанавливаем клавиши управления перемещением камеры
        # словарь, хранящий флаги нажатия клавиш
        self.keys = dict()
        # заполняем словарь
        for key in ['a', 'd', 'w', 's', 'q', 'e', 'space']:
            # создаём запись в словаре
            self.keys[key] = 0
            # регистрируем событие на нажатие клавиши
            base.accept(key, self.setKey, [key, 1])
            # регистрируем событие на отжатие клавиши
            base.accept(key+'-up', self.setKey, [key, 0])

        # создание обходчика столкновений
        self.traverser = CollisionTraverser()
        # очередь обработки столкновений
        self.collisQueue = CollisionHandlerQueue()
        # узел для сферы столкновений
        self.collisNode = CollisionNode('CameraSphere')
        # устанавливаем маску проверки столкновений ОТ
        self.collisNode.setFromCollideMask(BitMask32.bit(1))
        # сбрасываем маску проверки столкновений ДО
        self.collisNode.setIntoCollideMask(BitMask32.allOff())
        # создаём сферу столкновения радиусом 0.95
        collisSphere = CollisionSphere(0, 0, 0, 0.95)
        # и прикрепляем к созданному ранее узлу
        self.collisNode.addSolid(collisSphere)
        # закрепляем узел на камере
        self.collisCamNode = base.camera.attachNewNode(self.collisNode)
        # уведомляем обходчик о новом «объекте ОТ»
        self.traverser.addCollider(self.collisCamNode, self.collisQueue)

        # ускорение падения
        self.fall_acceleration = 0.015
        # величина силы прыжка
        self.jump_power = 0.21

        # скорость падения
        self.fall_speed = 0
        # флаг касания земли
        self.ground = False

        # режим редактирования
        self.edit_mode = True

        # устанавливаем режим редактирования
        self.setEditMode(self.edit_mode)


    # Метод установки режима редактирования
    def setEditMode(self, mode ):
        self.edit_mode = mode
        if not self.edit_mode:
            self.key_step = 0.1
        else:
            self.key_step = 0.2
            self.fallspeed = 0
            self.ground = False
            base.camera.setZ(30)


    # Метод установки состояния клавиши
    def setKey(self, key, value):
        self.keys[key] = value

    # Метод управления положением и ориентацией камеры
    def controlCamera(self, task):
        # сохраните предыдущую позицию камеры
        old_pos = base.camera.getPos()

        # рассчитываем смещения положения камеры по осям X Y Z
        move_x = self.key_step * (self.keys['d'] - self.keys['a'])
        move_y = self.key_step * (self.keys['w'] - self.keys['s'])
        move_z = self.key_step * (self.keys['e'] - self.keys['q'])

        # сохраните наклон камеры по вертикали
        old_pitch = base.camera.getP()
        # сбросьте наклон в 0 - ходим прямо без наклона
        base.camera.setP(0)
        # смещаем позицию камеры относительно предыдущего положения камеры
        base.camera.setPos(base.camera, move_x, move_y, move_z)
        # восстановите наклон
        base.camera.setP(old_pitch)

        if not self.edit_mode:
            old_z = base.camera.getZ()

            if not self.ground:
                self.fallspeed += self.g
                base.camera.setZ(old_z - self.fallspeed)
            # если есть столкновения с блоками
            if self.checkCollide():
                # восстанавите старую позицию камеры
                base.camera.setPos(old_pos)
                self.fallspeed = 0
                self.ground = True
            else:
                self.ground = False

            if self.ground and self.keys["space"]:
                self.grround = False
                self.fallspeed = -self.jump

        # получаем новое положение курсора мышки
        new_mouse_pos = base.win.getPointer(0)
        new_x = new_mouse_pos.getX()
        new_y = new_mouse_pos.getY()
        # пробуем установить курсор в центр экрана
        if base.win.movePointer(0, self.x_center, self.y_center):
            # рассчитываем поворот камеры по горизонтали
            self.heading = self.heading - (new_x - self.x_center) * self.mouse_step
            # рассчитываем наклон камеры по вертикали
            self.pitch = self.pitch - (new_y - self.y_center) * self.mouse_step
            if self.pitch > 80:
                self.pitch = 80
            if self.pitch < -80:
                self.pitch = -80
            # устанавливаем новую ориентацию камеры
            base.camera.setHpr(self.heading, self.pitch, 0)

        # сообщаем о необходимости повторного запуска задачи
        return task.again

    # Метод проверки столкновений с объектами
    def collisionTest(self):
        # запускаем обходчик на проверку
        self.traverser.traverse(base.render)

        # если обходчик обнаружил какие-то столкновения
        if self.collisQueue.getNumEntries() > 0:
            return True
        else:
            return False

    def checkCollide(self):
        self.traverser.traverse(base.render)
        if self.collisQueue.getNumEntries() > 0:
            return 1
        else:
            return 0
            
if __name__ == '__main__':
    # отладка модуля

    class MyApp(ShowBase):

        def __init__(self):
            ShowBase.__init__(self)

            # Загрузка модели
            self.model = loader.loadModel('models/environment')
            # Перемещаем модель в рендер
            self.model.reparentTo(render)
            # Устанавливаем масштаб и позицию для модели
            self.model.setScale(0.1)
            self.model.setPos(-2, 15, -3)

            # создаем контроллер мышки и клавиатуры
            self.controller = Controller()


    app = MyApp()
    app.run()