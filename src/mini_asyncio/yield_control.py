
class _YieldControl:
    
    def __await__(self):
        yield None

def yield_control():
    
    return _YieldControl()