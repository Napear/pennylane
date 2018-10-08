import autograd
import autograd.numpy as np


class GradientDescentOptimizer(object):
    """Base class for gradient-descent-based optimizers."""

    def __init__(self, stepsize=0.01):
        self.stepsize = stepsize

    def step(self, objective_fn, x, grad_fn=None):
        """Update x with one step of the optimizer."""

        x_shape = x.shape

        g = self.compute_grad(objective_fn, x, grad_fn=grad_fn)

        if len(x_shape) > 1:  # reshape gradient after grad() flattened it
            g = g.reshape(x_shape)

        x_out = self.apply_grad(g, x)

        return x_out

    def compute_grad(self, objective_fn, x, grad_fn=None):
        """Compute gradient of objective_fn at the point x"""
        if grad_fn is not None:
            g = grad_fn(x)  # just call the supplied grad function
        else:
            g = autograd.grad(objective_fn)(x)  # default is autograd
        return g

    def apply_grad(self, grad, x):
        """Update x to take a single optimization step"""
        return x - self.stepsize * grad


class MomentumOptimizer(GradientDescentOptimizer):
    """Gradient-descent optimizer with momentum."""

    def __init__(self, stepsize=0.01, momentum=0.9):
        super().__init__(stepsize)
        self.momentum = momentum
        self.accumulation = None

    def apply_grad(self, grad, x):
        """Update x to take a single optimization step."""
        if self.accumulation is None:
            self.accumulation = self.stepsize * grad
        else:
            self.accumulation = self.momentum * self.accumulation + self.stepsize * grad
        return x - self.accumulation

    def reset(self):
        """Reset optimizer by erasing memory of past steps."""
        self.accumulation = None


class NesterovMomentumOptimizer(MomentumOptimizer):
    """Gradient-descent optimizer with Nesterov momentum."""

    def __init__(self, stepsize=0.01, momentum=0.9):
        super().__init__(stepsize, momentum)

    def compute_grad(self, objective_fn, x, grad_fn=None):
        """Compute gradient of objective_fn at the shifted point (x - momentum*accumulation) """

        if self.accumulation is None:
            shifted_x = x
        else:
            shifted_x = x - self.momentum * self.accumulation

        if grad_fn is not None:
            g = grad_fn(shifted_x)  # just call the supplied grad function
        else:
            g = autograd.grad(objective_fn)(shifted_x)  # default is autograd
        return g


class AdagradOptimizer(GradientDescentOptimizer):
    """Gradient-descent optimizer with past-gradient-dependent learning rate in each dimension."""

    def __init__(self, stepsize=0.01):
        super().__init__(stepsize)
        self.accumulation = None

    def apply_grad(self, grad, x):
        """Update x to take a single optimization step."""
        if self.accumulation is None:
            self.accumulation = grad * grad
        else:
            self.accumulation += grad * grad
        return x - (self.stepsize / np.sqrt(self.accumulation + 1e-8)) * grad  # elementwise multiplication

    def reset(self):
        """Reset optimizer by erasing memory of past steps."""
        self.accumulation = None


class RMSPropOptimizer(AdagradOptimizer):
    """Adagrad optimizer with decay of learning rate adaptation."""

    def __init__(self, stepsize=0.01, decay=0.9):
        super().__init__(stepsize)
        self.decay = decay

    def apply_grad(self, grad, x):
        """Update x to take a single optimization step."""
        if self.accumulation is None:
            self.accumulation = (1 - self.decay) * (grad * grad)
        else:
            self.accumulation = self.decay * self.accumulation + (1 - self.decay) * (grad * grad)  # elementwise multiplication
        return x - (self.stepsize / np.sqrt(self.accumulation + 1e-8)) * grad  # elementwise multiplication


class AdamOptimizer(GradientDescentOptimizer):
    """Gradient-descent optimizer with adaptive learning rate, first and second moment."""

    def __init__(self, stepsize=0.01, beta1=0.9, beta2=0.99):
        super().__init__(stepsize)
        self.beta1 = beta1
        self.beta2 = beta2
        self.stepsize = stepsize
        self.firstmoment = None
        self.secondmoment = None
        self.t = 0

    def apply_grad(self, grad, x):
        """Update x to take a single optimization step."""

        self.t += 1

        # Update first moment
        if self.firstmoment is None:
            self.firstmoment = grad
        else:
            self.firstmoment = self.beta1 * self.firstmoment + (1 - self.beta1) * grad

        # Update second moment
        if self.secondmoment is None:
            self.secondmoment = grad * grad
        else:
            self.secondmoment = self.beta2 * self.secondmoment + (1 - self.beta2) * (grad * grad)

        # Update step size (instead of correcting for bias)
        adapted_stepsize = self.stepsize * np.sqrt(1 - self.beta2**self.t) / (1 - self.beta1**self.t)

        return x - adapted_stepsize * self.firstmoment / (np.sqrt(self.secondmoment) + 1e-8)

    def reset(self):
        """Reset optimizer by erasing memory of past steps."""
        self.firstmoment = None
        self.secondmoment = None
        self.t = 0