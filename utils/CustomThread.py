from time import sleep
import threading
from _thread import interrupt_main
import sys
from io import StringIO


class CustomThread(threading.Thread):
    # self._stopper = threading.Event()
    
    def __init__(self, *args, **kwargs):
        super(CustomThread, self).__init__(*args, **kwargs)
        self._stopper = threading.Event()

    def stop(self):
        self._stopper.set()

    # def stopped(self):
    #     return self._stopper.is_set()

    def run(self):
        sleep(10)
        # interrupt_main()
        # self._stopper.set()
        # while (True):
        #     pass
        # sleep(10)
        if not self._stopper.is_set():
            interrupt_main()



def runCode(code, myglobals):
    oldStdOUT = sys.stdout
    redirectedOutput = sys.stdout = StringIO()
    oldStdERR = sys.stderr
    redirectedOutput2 = sys.stderr = StringIO()
    result = ""
    try:
        thread = CustomThread(daemon=True)
        # thread.daemon = True
        thread.start()
        exec(code, myglobals)
        thread.stop()
        result = redirectedOutput.getvalue()
    except Exception as e:
        # self._stopper.set()
        # thread.stop()
        
        result = repr(e)
    except SystemExit as s:
        # thread.stop()
        result = redirectedOutput2.getvalue()
    except KeyboardInterrupt as k:
        # thread.stop()
        result = "timed out"
    
    thread.stop()
    # thread.join()

    myglobals.popitem()
    sys.stdout = oldStdOUT
    sys.stderr = oldStdERR

    return result

# =================================================================================================
# =================================================================================================
# =================================================================================================
# =================================================================================================
# import threading
# import sys
# from io import StringIO
# from time import sleep


# class CustomThread(threading.Thread):
#     def __init__(self, *args, **kwargs):
#         super(CustomThread, self).__init__(*args, **kwargs)
#         self._stopper = threading.Event()
#         self.exc_info = None

#     def stop(self):
#         self._stopper.set()

#     def stopped(self):
#         return self._stopper.is_set()
    
#     def start(self, code, myglobals):
#         self._stopper.clear()
#         self.run(code, myglobals)
#         # Execute the code
#         exec(code, myglobals)

#     def run(self, code, myglobals):
#         try:
#             sleep(5)
#             if not self.stopped():
#                 # Simulate an exception
#                 raise TimeoutError("Execution timed out")

#         except Exception as e:
#             self.exc_info = sys.exc_info()
#         except TimeoutError as e:
#             result = "Execution timed out"


# def runCode(code, myglobals):
#     oldStdOUT = sys.stdout
#     redirectedOutput = sys.stdout = StringIO()
#     oldStdERR = sys.stderr
#     redirectedOutput2 = sys.stderr = StringIO()
#     result = ""
#     thread = CustomThread()
#     try:
#         thread.start(code, myglobals)

#         # time.sleep(0.1)
#         # thread.join(5.1)  # Wait for the thread to finish with a timeout
#         if thread.exc_info:
#             # Re-raise the exception
#             raise thread.exc_info[0](thread.exc_info[1]).with_traceback(thread.exc_info[2])
#         result = redirectedOutput.getvalue()
#     except Exception as e:
#         # print(repr(e))
#         result = repr(e)
#         # result = ""
#     finally:
#         thread.stop()
#         myglobals.popitem()
#         sys.stdout = oldStdOUT
#         sys.stderr = oldStdERR
#     return result



# code = """
# def fib(n: int):
#     if n == 0:
#         return 0
#     if n == 1:
#         return 1
#     return fib(n - 1) + fib(n - 2)

# import unittest

# class TestFib(unittest.TestCase):
#     def test_fib_of_0(self):
#         self.assertEqual(fib(0), 0)

#     def test_fib_of_1(self):
#         self.assertEqual(fib(1), 1)

#     def test_fib_of_2(self):
#         self.assertEqual(fib(2), 1)

#     def test_fib_of_3(self):
#         self.assertEqual(fib(3), 2)

#     def test_fib_of_8(self):
#         self.assertEqual(fib(8), 21)

#     def test_fib_of_10(self):
#         self.assertEqual(fib(10), 55)

#     def test_fib_of_10(self):
#         self.assertEqual(fib(50), 55)

# if __name__ == '__main__':
#     unittest.main(argv=['first-arg-is-ignored'])()
# """

# print(runCode(code, globals()))
