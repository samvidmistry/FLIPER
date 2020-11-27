from lark import Lark
from PIL import Image, ImageDraw

with open('grammar.lark', 'w') as f:
    fliperGrammer = f.readlines()

parser = Lark(fliperGrammer)

