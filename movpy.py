
st = "hello world"
x=''.join(format(ord(x), 'b') for x in st)

print(len(x))

a = str(x)
print(type(a))
b = len(a)
print(type(b))