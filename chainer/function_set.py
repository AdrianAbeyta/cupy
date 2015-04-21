import numpy
from pycuda import gpuarray
from chainer import Function

def _to_gpu(array):
    if type(array) == numpy.ndarray:
        return gpuarray.to_gpu(array)
    return array

def _to_cpu(array):
    if type(array) == gpuarray.GPUArray:
        return array.get()
    return array

class FunctionSet(object):
    """Manager of a set of functions.

    User typically stores parameterized functions into FunctionSet. FunctionSet
    makes it easy to controll cpu/gpu migration and manage the list of
    parameters/gradients.

    """
    def __init__(self, **functions):
        self.functions = {}
        for name, func in functions.iteritems():
            self[name] = func

    def __setitem__(self, name, func):
        assert isinstance(func, Function)
        self.functions[name] = func
        setattr(self, name, func)

    def __getitem__(self, name):
        return self.functions[name]

    def __delitem__(self, name):
        del self.functions[name]
        delattr(self, name)

    def collect_parameters(self):
        """Collect parameters and gradients."""
        return self.parameters, self.gradients

    def to_gpu(self):
        """Move all parameters and gradients to GPU."""
        for func in self.functions.itervalues():
            params = func.parameters
            func.parameters = (_to_gpu(w) for w in params)
            grads  = func.gradients
            func.gradients  = (_to_gpu(g) for g in grads)

    def to_cpu(self):
        """Move all parameters and gradients to CPU."""
        for func in self.functions.itervalues():
            params = func.parameters
            func.parameters = (_to_cpu(w) for w in params)
            grads  = func.gradients
            func.gradients  = (_to_cpu(g) for g in grads)

    @property
    def parameters(self):
        return sum((func.parameters for _, func in self._get_sorted_funcs()), ())

    @parameters.setter
    def parameters(self, params):
        param_iter = iter(params)
        for _, func in self._get_sorted_funcs():
            func.parameters = param_iter

    @property
    def gradients(self):
        return sum((func.gradients for _, func in self._get_sorted_funcs()), ())

    @gradients.setter
    def gradients(self, grads):
        grad_iter = iter(grads)
        for _, func in self._get_sorted_funcs():
            func.gradients = grad_iter

    def _get_sorted_funcs(self):
        return sorted(self.functions.iteritems())
