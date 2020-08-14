import json
import os
import sys

from PIL import Image, ImageDraw

from utils.reader import Reader


def _(*args):
    print(f'[SC Tool] ', end='')
    for arg in args:
        print(arg, end=' ')
    print()


def _i(text: str):
    return input(f'[SC Tool] {text}: ')


def _e(*args):
    print('[Error] ', end='')
    for arg in args:
        print(arg, end=' ')
    print()
    input('Press Enter to exit: ')
    sys.exit()


class SC(Reader):
    def readString(self) -> str:
        length = self.readUShort()
        return self.readChar(length)

    def readPngChunk(self) -> bytes:
        length = self.readUInt32()
        _type = self.read(4)
        chunk_data = self.read(length)
        crc = self.read(4)
        return length.to_bytes(4, 'big') + _type + chunk_data + crc

    def __init__(self, filename: str):
        self.basename = filename.split('.dat')[0]

        self.texture = Image.open(open(f'png/{self.basename}.png', 'rb'))

        with open(filename, 'rb') as fh:
            super().__init__(fh.read())
            fh.close()

        sprites_export_path = f'sprites/{self.basename}'

        if not os.path.exists(sprites_export_path):
            os.mkdir(sprites_export_path)

        textures_export_path = f'textures/{self.basename}'

        if not os.path.exists(textures_export_path):
            os.mkdir(textures_export_path)

        exports_count = self.readUShort()
        for x in range(exports_count):
            name = self.readString()
            start_pos = (self.readUShort(), self.readUShort())
            size = (self.readUShort(), self.readUShort())
            polygon = [start_pos, (start_pos[0] + size[0], start_pos[1]),
                       (start_pos[0], start_pos[1]+size[1]), (start_pos[0] + size[0], start_pos[1]+size[1])]
            polygon[2], polygon[3] = polygon[3], polygon[2]
            region = self.generate_region(polygon)
            region.save(f'{sprites_export_path}/{name}.png')

        textures_count = self.readUShort()
        for x in range(textures_count):
            name = self.readString()
            group_maybe = self.readString()
            size_x = self.readUShort()
            size_y = self.readUShort()
            self.read(4)
            file_data = self.read(8)
            file_data += self.readPngChunk()
            file_data += self.readPngChunk()
            file_data += self.readPngChunk()

            export_name = f'{textures_export_path}/{name}'
            export_path = export_name + '.png'

            i = 0
            while os.path.exists(export_path):
                export_path = export_name + '_' + str(i) + '.png'
                i += 1

            with open(export_path, 'wb') as fh:
                fh.write(file_data)
                fh.close()

    def generate_region(self, polygon: list):
        size = self.texture.size

        imMask = Image.new('L', size, 0)
        ImageDraw.Draw(imMask).polygon(polygon, fill=255)
        bbox = imMask.getbbox()
        if bbox:
            region_size = (bbox[2] - bbox[0], bbox[3] - bbox[1])
            tmpRegion = Image.new('RGBA', region_size, None)
            tmpRegion.paste(self.texture.crop(bbox), None, imMask.crop(bbox))

            return tmpRegion


if __name__ == '__main__':
    if not os.path.exists('textures'):
        os.mkdir('textures')
    if not os.path.exists('sprites'):
        os.mkdir('sprites')
    if not os.path.exists('png'):
        os.mkdir('png')

    sc = SC(_i('DAT File Name'))
