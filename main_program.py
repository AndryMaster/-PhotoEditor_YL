import os
import sys
from PIL import Image, ImageFilter

from styles import Ui_PhotoEditorWindow, Ui_CropImageWindow, Ui_SearchFileForm
from db import save_file_path, get_last_paths, delete_all_paths
from logfile import input_log, MES, ER, END

from PyQt5.QtGui import QPixmap, QIcon
from PyQt5.QtCore import Qt, QPointF, QRect
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget
from PyQt5.QtWidgets import QFileDialog, QMessageBox, QInputDialog, QRubberBand, QAction


class MyProgram(QMainWindow, Ui_PhotoEditorWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.changed = False
        self.setFixedSize(self.geometry().width(), self.geometry().height())
        input_log(MES, 'Start program')

        window_icon = QIcon('icons/pe_full_colored.ico')  # Icon: icons/pe(_full)(_colored).ico
        self.setWindowIcon(window_icon)

        # File searching
        self.open_search_file_widget()

        # Window buttons
        self.update_btn.clicked.connect(self.update_image)
        self.btn_open_file.clicked.connect(self.open_search_file_widget)
        self.btn_clear_all_params.clicked.connect(self.clear_all_params)

        # Stage 1 (colors)
        self.contrast.toggled.connect(self.update_show_btn)
        self.level_contrast.hide()

        # Stage 2 (filters)
        self.blur.toggled.connect(self.update_show_btn)
        self.blur_spin.hide()

        # Stage 3 (settings)
        self.slider_rotate.valueChanged.connect(self.update_show_btn)
        self.btn_crop_image.clicked.connect(self.crop_image_start)
        self.btn_delete_crops.clicked.connect(self.delete_crops)
        self.put_rotate.setDisabled(True)
        self.put_width.setDisabled(True)
        self.put_height.setDisabled(True)

        # Stage 4 (save)
        self.btn_save.clicked.connect(self.save_img)
        self.btn_save_and_close.clicked.connect(self.save_img_and_close)
        self.btn_change_directory.clicked.connect(self.change_directory)
        self.btn_change_fname.clicked.connect(self.change_fname)
        self.btn_change_exp.clicked.connect(self.change_exp)

    def start_program(self, fname):
        self.show()

        self.file_name = fname
        name = fname.split('/')[-1]
        self.name_of_image, self.ext = name.split('.')
        save_file_path(fname, redacted=False)

        self.update_title()
        self.put_directory.clear()
        self.put_directory.appendPlainText('/'.join(self.file_name.split('/')[:-1]))
        self.put_fname.setText(self.name_of_image)
        self.put_image_exp.setText(self.ext)

        img_original = Image.open(fname)
        img = img_original.resize(self.get_resized((800, 600), *img_original.size))
        img_small_orig = img_original.resize(self.get_resized((200, 150), *img_original.size))
        self.update_size(*img_original.size)

        img_original.save(f'temp/image_original.{self.ext}')
        img_original.save(f'temp/image_original_full_size.{self.ext}')
        img.save(f'temp/image.{self.ext}')
        img_small_orig.save(f'temp/image_small_orig.{self.ext}')

        self.pixmap = QPixmap(f'temp/image_small_orig.{self.ext}')
        self.orig_image_place.setPixmap(self.pixmap)
        self.pixmap = QPixmap(f'temp/image.{self.ext}')
        self.image_place.setPixmap(self.pixmap)
        input_log(MES, f'Get image path: <{fname}>')
        self.clear_all_params()

    def update_image(self, save_image=False):
        self.changed = True
        image = Image.open(f'temp/image_original.{self.ext}')

        # Stage 1 (colors)
        k_light = int(self.slider_light.value()) * 2 / int(self.slider_light.maximum())
        if k_light < 1:
            k_light = 0.5 + k_light / 2
        kr = int(self.slider_r.value()) / int(self.slider_r.maximum())
        kg = int(self.slider_g.value()) / int(self.slider_g.maximum())
        kb = int(self.slider_b.value()) / int(self.slider_b.maximum())
        inverse = self.inverse.isChecked()
        bw = self.bw.isChecked()

        if (not all([elem == 1 for elem in [k_light, kr, kg, kb]])) or inverse or bw:
            pixels = image.load()
            x, y = image.size
            for i in range(x):
                for j in range(y):
                    r, g, b = pixels[i, j]
                    r = self.cor_pix(r * kr * k_light)
                    g = self.cor_pix(g * kg * k_light)
                    b = self.cor_pix(b * kb * k_light)
                    if inverse:
                        r, g, b = 255 - r, 255 - g, 255 - b
                    if bw:
                        k_bw = round(0.299 * r + 0.587 * g + 0.115 * b)
                        # k_bw = round((r + g + b) / 3)
                        r, g, b = k_bw, k_bw, k_bw
                    pixels[i, j] = r, g, b

        if self.contrast.isChecked() and self.level_contrast.value() != 0:
            def contrast(c):
                value = 128 + factor * (c - 128)
                return max(0, min(255, value))
            level = self.level_contrast.value() * 10
            factor = (259 * (level + 255)) / (255 * (259 - level))
            image = image.point(contrast)

        # Stage 2 (filters)
        try:
            filters = {
                'BLUR': self.blur.isChecked(),
                'CONTOUR': self.contur.isChecked(),
                'DETAIL': self.detalize.isChecked(),
                'EDGE_ENHANCE': self.edge.isChecked(),
                'EDGE_ENHANCE_MORE': self.edge_plus.isChecked(),
                'EMBOSS': self.emboss.isChecked(),
                'FIND_EDGES': self.find_edges.isChecked(),
                'SMOOTH': self.smooth.isChecked(),
                'SMOOTH_MORE': self.smooth_more.isChecked(),
                'SHARPEN': self.sharpen.isChecked()
            }
            if filters['SHARPEN']:
                image = image.filter(ImageFilter.SHARPEN)
            else:
                if filters['CONTOUR']:
                    image = image.filter(ImageFilter.CONTOUR)
                if filters['DETAIL']:
                    image = image.filter(ImageFilter.DETAIL)
                if filters['EDGE_ENHANCE']:
                    image = image.filter(ImageFilter.EDGE_ENHANCE)
                if filters['EDGE_ENHANCE_MORE']:
                    image = image.filter(ImageFilter.EDGE_ENHANCE_MORE)
                if filters['EMBOSS']:
                    image = image.filter(ImageFilter.EMBOSS)
                if filters['FIND_EDGES']:
                    image = image.filter(ImageFilter.FIND_EDGES)
                if filters['SMOOTH']:
                    image = image.filter(ImageFilter.SMOOTH)
                if filters['SMOOTH_MORE']:
                    image = image.filter(ImageFilter.SMOOTH_MORE)
            if filters['BLUR']:
                image = image.filter(ImageFilter.GaussianBlur(radius=self.blur_spin.value()))
        except Exception as ex:
            input_log(ER, f'Image filters error: {ex}')

        # Stage 3 (settings)
        image = self.rotate_img(image)
        if self.k_size_spin.value() != 1.0 or int(self.slider_rotate.value()):
            self.update_size(*image.size)

        ####################################################################
        if save_image:
            return image

        img = image.resize(self.get_resized((800, 600), *image.size))
        img.save(f'temp/image.{self.ext}')
        self.pixmap = QPixmap(f'temp/image.{self.ext}')
        self.image_place.setPixmap(self.pixmap)
        input_log(MES, 'Image was updated')
        self.status_save.setText('')
        self.update_title()

    def clear_all_params(self):
        self.slider_r.setValue(10)
        self.slider_g.setValue(10)
        self.slider_b.setValue(10)
        self.slider_light.setValue(10)
        self.slider_rotate.setValue(0)
        self.k_size_spin.setValue(1.0)
        self.inverse.setChecked(False)
        self.bw.setChecked(False)
        self.contrast.setChecked(False)
        self.no_blur.setChecked(False)
        self.no_detalize.setChecked(False)
        self.no_edge.setChecked(False)
        self.no_spec.setChecked(False)
        self.no_smooth.setChecked(False)
        self.no_sharpen.setChecked(False)
        self.left_to_right.setChecked(False)
        self.top_to_bottom.setChecked(False)

        self.update_show_btn()
        self.delete_crops()
        self.update_image()

    def update_title(self):
        self.setWindowTitle(f'Abobe Photoshop - {self.name_of_image}' +
                            f'.{self.ext}{"*" if self.changed else ""}')

    def update_show_btn(self):
        self.level_contrast.show() if self.contrast.isChecked() else self.level_contrast.hide()
        self.blur_spin.show() if self.blur.isChecked() else self.blur_spin.hide()
        self.put_rotate.setText(str(int(self.slider_rotate.value()) * -90))

    def update_size(self, width, height):
        k = self.k_size_spin.value()
        self.put_width.setText(str(round(width * k)))
        self.put_height.setText(str(round(height * k)))
        return round(width * k), round(height * k)

    def open_search_file_widget(self):  # File searching
        self.hide()
        self.find_example = SearchFileWidget()
        self.find_example.setFixedSize(self.find_example.geometry().width(),
                                       self.find_example.geometry().height())
        self.find_example.show()

    def rotate_img(self, image, roll_back=False):
        flip_left_right = self.left_to_right.isChecked()
        flip_top_bottom = self.top_to_bottom.isChecked()
        rotate = int(self.slider_rotate.value()) * 90
        if roll_back:
            rotate = -rotate
        if flip_left_right and not roll_back:
            image = image.transpose(Image.FLIP_LEFT_RIGHT)
        if flip_top_bottom and not roll_back:
            image = image.transpose(Image.FLIP_TOP_BOTTOM)
        if rotate == 90 or rotate == -270:
            image = image.transpose(Image.ROTATE_90)
        elif rotate == 180 or rotate == -180:
            image = image.transpose(Image.ROTATE_180)
        elif rotate == 270 or rotate == -90:
            image = image.transpose(Image.ROTATE_270)
        if flip_left_right and roll_back:
            image = image.transpose(Image.FLIP_LEFT_RIGHT)
        if flip_top_bottom and roll_back:
            image = image.transpose(Image.FLIP_TOP_BOTTOM)
        return image

    def keyPressEvent(self, event):
        if int(event.modifiers()) == Qt.CTRL:
            if event.key() == Qt.Key_S:
                self.save_img()
            if event.key() == Qt.Key_C:
                self.crop_image_start()

    def save_img(self):
        try:
            self.changed = False
            file_path = f'{self.put_directory.toPlainText()}/' \
                        f'{self.put_fname.text()}.{self.put_image_exp.text()}'
            image = self.update_image(save_image=True)
            image = image.resize(self.update_size(*image.size)) if self.k_size_spin == 1 else image
            image.save(file_path)
            save_file_path(file_path, redacted=True)
            self.update_title()
        except Exception as ex:
            self.status_save.setText('*Ошибка сохранения')
            input_log(ER, f'Saving error: {ex}')
        else:
            self.status_save.setText('*Успешно сохранено')
            input_log(MES, 'Image saved')

    def save_img_and_close(self):
        self.save_img()
        self.close()

    def change_directory(self):
        options = QFileDialog.DontResolveSymlinks | QFileDialog.ShowDirsOnly
        direct = QFileDialog.getExistingDirectory(self, "Выбор папки", options=options)
        if direct:
            self.put_directory.clear()
            self.put_directory.appendPlainText(direct)

    def change_fname(self):
        fname, ok_pressed = QInputDialog.getText(
            self, "Имя файла", "Введите имя изображения:",
            text=self.put_fname.text())
        if ok_pressed and fname:
            self.put_fname.setText(fname[:22])

    def change_exp(self):
        all_ext = ['jpg', 'jpeg', 'png', 'bmp']
        del all_ext[all_ext.index(self.ext)]
        ext, ok_pressed = QInputDialog.getItem(
            self, "Расширение изображения", "Выберите расширение:",
            (self.ext + ' (рекомендуемое)', *all_ext), 0, False)
        if ok_pressed:
            self.put_image_exp.setText(ext.split()[0])

    def delete_crops(self):
        img = Image.open(f"temp/image_original_full_size.{self.ext}")
        self.update_size(*img.size)
        img.save(f"temp/image_original.{self.ext}")
        self.update_image()

    def crop_image_start(self):
        img = self.update_image(save_image=True)  # rotated
        xi, yi, k, mx, my = self.get_resized((800, 600), *img.size, kof=True)
        self.update_image()
        self.crop_example = ImageCroppingWindow(
            img=f"temp/image.{self.ext}", k=k,
            margin_x=mx, margin_y=my)
        self.crop_example.setFixedSize(self.crop_example.geometry().width(),
                                       self.crop_example.geometry().height())
        self.crop_example.show()
        self.hide()

    def crop_image_end(self, coords=None):
        self.show()
        if coords is None:
            coords = []
        if coords:
            img = Image.open(f"temp/image_original.{self.ext}")

            # rotate image
            img = self.rotate_img(img)

            img = img.crop(tuple(coords))
            self.update_size(*img.size)

            # come back rotate image
            img = self.rotate_img(img, roll_back=True)

            img.save(f"temp/image_original.{self.ext}")
            self.update_image()

    def clear(self):
        try:
            os.remove(f"temp/image_original.{self.ext}")
            os.remove(f'temp/image_original_full_size.{self.ext}')
            os.remove(f"temp/image.{self.ext}")
            os.remove(f"temp/image_small_orig.{self.ext}")
        except Exception as ex:
            input_log(ER, f'Error cleaning needless images: {ex}')
        else:
            input_log(MES, 'Clean needless images in temp')

    def closeEvent(self, event):
        self.clear()
        input_log(MES, END)

    @staticmethod
    def get_resized(size, x, y, kof=False):
        if kof:
            k = max(round(x / size[0], 3), round(y / size[1], 3))
            x_im, y_im = round(x / k), round(y / k)
            margin_x, margin_y = round((size[0] - x_im) / 2), round((size[1] - y_im) / 2)
            return x_im, y_im, k, margin_x, margin_y
        else:
            k = max(round(x / size[0], 2), round(y / size[1], 2))
            return round(x / k), round(y / k)

    @staticmethod
    def cor_pix(pix):
        pix = round(pix)
        if pix < 0:
            return 0
        elif pix > 255:
            return 255
        else:
            return pix
        # return max(0, min(255, round(pix)))


class ImageCroppingWindow(QMainWindow, Ui_CropImageWindow):
    def __init__(self, img, k, margin_x, margin_y):
        super().__init__()
        self.setupUi(self)
        self.k = k
        self.margin_x = margin_x
        self.margin_y = margin_y
        self.margin_menu = 23
        self.result_coords = []
        self.screenshot = True
        self.save = False
        self.image = QPixmap(img)
        self.put_image.setPixmap(self.image)
        input_log(MES, 'Open: Image Crop Window')

        window_icon = QIcon('icons/pe_full_colored.ico')  # Icon: icons/pe(_full)(_colored).ico
        self.setWindowIcon(window_icon)

        main_menu_bar = self.menuBar()
        vide_menu = main_menu_bar.addMenu("Выделение")
        actions = main_menu_bar.addMenu("Действия")

        vide_line = QAction("Выделить область", self)
        vide_menu.addAction(vide_line)
        vide_line.triggered.connect(self.screenshot_on)

        vide_pass = QAction("Свободный режим", self)
        vide_menu.addAction(vide_pass)
        vide_pass.triggered.connect(self.screenshot_off)

        action = QAction("Обрезать изображение", self)
        actions.addAction(action)
        action.triggered.connect(self.save_and_exit)

        action = QAction("Выйти без изменений", self)
        actions.addAction(action)
        action.triggered.connect(self.exit)

        self.selection = QRubberBand(QRubberBand.Rectangle, self)
        self.selection.hide()
        self.start = QPointF()
        self.end = QPointF()

    def is_on_image(self, event):
        if 0 + self.margin_x <= event.x() <= self.put_image.width() - self.margin_x and \
                0 + self.margin_y <= event.y() - self.margin_menu <= self.put_image.height() - self.margin_y:
            return True
        return False

    def mousePressEvent(self, event):  # press
        if self.screenshot and self.is_on_image(event) and event.buttons() == Qt.LeftButton:
            self.start = event.pos()
            self._start = event.globalPos()

    def mouseMoveEvent(self, event):  # move
        if self.screenshot and self.is_on_image(event) and event.buttons() == Qt.LeftButton:
            self.end = event.pos()
            self.selection.setGeometry(QRect(self.start, self.end).normalized())
            self.selection.show()

    def mouseReleaseEvent(self, event):  # stop move
        input_log(MES, 'User finished drawing the crop rectangle')
        if self.screenshot:  # and self.is_on_image(event):
            self._end = event.globalPos()
            x = [round((self.start.x() - self.margin_x) * self.k),
                 round((self.end.x() - self.margin_x) * self.k)]
            y = [round((self.start.y() - self.margin_y - self.margin_menu) * self.k),
                 round((self.end.y() - self.margin_y - self.margin_menu) * self.k)]
            self.result_coords = [min(x), min(y), max(x), max(y)]

    def screenshot_on(self):
        self.screenshot = True

    def screenshot_off(self):
        self.screenshot = False
        self.selection.hide()

    def save_and_exit(self):
        self.save = True
        self.close()

    def exit(self):
        self.close()

    def closeEvent(self, event):
        input_log(MES, 'Closing: Image Crop Window')
        if self.save:
            input_log(MES, 'User crop image')
            example.crop_image_end(coords=self.result_coords)
        else:
            input_log(MES, 'User don`t crop image')
            example.crop_image_end()


class SearchFileWidget(QWidget, Ui_SearchFileForm):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.btn_select_file.clicked.connect(self.select_file)
        self.btn_last_images.clicked.connect(self.last_images)
        self.file_combo.activated.connect(self.combo)
        self.btn_actions.clicked.connect(self.search_actions)
        self.btn_ok.clicked.connect(self.ok)
        self.btn_ok.setDisabled(True)
        self.btn_canel.setDisabled(True)
        self.file_combo.hide()
        self.btn_actions.hide()
        self.act = {'NONE': 1,
                    'REDACTED': 2,
                    'NO REDACTED': 3}
        self.fill_combo(search_filter=self.act['NONE'])
        window_icon = QIcon('icons/file_full_colored.ico')  # Icon: icons/file(_full)_colored.ico
        self.setWindowIcon(window_icon)
        input_log(MES, 'Create SearchFileWidget')

    def enabled_buttons(self):
        self.btn_ok.setDisabled(False)
        self.is_file.setText('')

    def update_fname_text(self, text):
        self.file_name_place.clear()
        self.file_name_place.setPlainText(text)

    def select_file(self):
        self.file_name = QFileDialog.getOpenFileName(
            self, 'Выбор изображения', '', 'Изображения (*.jpg *.jpeg *.png *.bmp)')[0]
        self.update_fname_text(self.file_name)
        self.enabled_buttons()

    def last_images(self):
        if self.file_combo.isHidden():
            self.file_combo.show()
            self.btn_actions.show()
        else:
            self.file_combo.hide()
            self.btn_actions.hide()

    def search_actions(self):
        actions = [
            'Показать все записи',
            'Показать не редактированные',
            'Показать редактированные',
            'Удалить все записи']
        action, ok_pressed = QInputDialog.getItem(self, "", "Выберите действие:", actions, 0, False)
        if ok_pressed:
            if action == actions[0]:
                self.fill_combo(search_filter=self.act['NONE'])
            elif action == actions[1]:
                self.fill_combo(search_filter=self.act['NO REDACTED'])
            elif action == actions[2]:
                self.fill_combo(search_filter=self.act['REDACTED'])
            elif action == actions[3]:
                answer = QMessageBox.question(
                    self, "Предупреждение", "Вы уверены что хотите удалить все записи?",
                    QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                if answer == QMessageBox.Yes:
                    delete_all_paths()
                    self.file_combo(search_filter=self.act['NONE'])

    def combo(self, index):
        self.file_name = self.last_files[index]
        self.update_fname_text(self.file_name)
        self.enabled_buttons()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Enter:
            self.exit()

    def exit(self):
        if os.path.isfile(self.file_name):
            input_log(MES, 'User select file name')
            example.start_program(fname=self.file_name)
            self.close()
        else:
            input_log(ER, 'This file name does not exist')
            self.is_file.setText('Ошибка: Такого файла не существует')

    def ok(self):
        self.exit()

    def fill_combo(self, search_filter):
        self.file_combo.clear()
        max_length = 37
        mid = '/...'

        if search_filter == self.act['REDACTED']:
            old_paths = get_last_paths(where='WHERE redacted = TRUE')
        elif search_filter == self.act['NO REDACTED']:
            old_paths = get_last_paths(where='WHERE redacted = FALSE')
        else:
            old_paths = get_last_paths()
        self.last_files = []
        for elem in old_paths[::-1]:
            path, date, redacted = elem
            redacted = 'Редактирован   ' if redacted else 'Не редактирован'
            s_path = path.split('/')
            if len(path) > max_length:
                short_path = s_path[0] + mid + path[-max_length + len(mid + s_path[0]):]
                res = '  '.join([short_path, date, redacted])
            else:
                res = '  '.join([path + ' ' * (max_length - len(path)), date, redacted])
            self.last_files.append(path)
            self.file_combo.addItem(res)


if __name__ == '__main__':
    app = QApplication(sys.argv)

    # My program starts
    example = MyProgram()

    sys.exit(app.exec_())
