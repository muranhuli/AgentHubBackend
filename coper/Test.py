from core.Computable import Computable
from coper.Add import Add

class Test(Computable):
    def compute(self, x, y):
        add = Add()
        return add(x,y)+add(x,y)
