from ipykernel.kernelapp import IPKernelApp
from . import PyStataKernel

IPKernelApp.launch_instance(kernel_class=PyStataKernel)
