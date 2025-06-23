# from threading import Event
# import asyncio

# class Animation:
#     """Class to handle loading animations."""
#     def __init__(self):
#         """Initialize the animation class."""
        
#         self.done = Event()  

#     async def loading_animation(self, message: str = "Loading"):
#         """
#         Start the loading animation.
#         """
#         while not self.done.is_set():
#             for i in ["/", "-", "\\", "|"]:
#                 print(f"\r{message}  {i}", end='', flush=True)
#                 await asyncio.sleep(0.5)

#     def stop_animation(self):
#         """
#         Stop the loading animation.
#         """
#         self.done.set()
        
    