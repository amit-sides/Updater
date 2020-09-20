import win32serviceutil
import win32service
import win32event
import win32file
import servicemanager
import logging

import settings
import updater


class UpdaterServerSvc(win32serviceutil.ServiceFramework):
    _svc_name_ = f"{settings.SOFTWARE_NAME}Updater"
    _svc_display_name_ = f"{settings.SOFTWARE_NAME} Updater"

    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.updater = None
        self.stop_event_handle = win32event.CreateEvent(None, 0, 0, None)
        self.running = False

    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.stop_event_handle)

    def SvcDoRun(self):
        servicemanager.LogMsg(servicemanager.EVENTLOG_INFORMATION_TYPE,
                              servicemanager.PYS_SERVICE_STARTED,
                              (self._svc_name_, ''))
        self.run()

    @staticmethod
    def setup_logger():
        logger_filepath = settings.LOGGER_PATH
        logging.basicConfig(filename=logger_filepath, level=logging.DEBUG, 
                            format="%(asctime)-19s [%(levelname)-8s] %(funcName)-20s | %(message)s",
                            datefmt="%d.%m.%Y %H:%M:%S")

    def run(self):
        # Setup the logger
        self.setup_logger()

        # Creates the updater
        self.updater = updater.Updater()
        self.running = True

        # Handling events...
        while self.running:
            # Creates an event to handle IO on the socket
            socket_event = win32event.CreateEvent(None, True, False, None)
            win32file.WSAEventSelect(self.updater.management_socket, socket_event, win32file.FD_READ | win32file.FD_CLOSE)

            # Waits for either an event on the socket or a stop request of the service, waits indefinitely
            event_result = win32event.WaitForMultipleObjects([socket_event, self.stop_event_handle], 0, win32event.INFINITE)
            if event_result == win32event.WAIT_TIMEOUT:
                # Timeout occurred, ignoring...
                pass
            elif event_result == win32event.WAIT_ABANDONED_0 + 0:
                # socket_event occurred, The socket has some IO that needs to be handled
                self.updater.receive_message()
                if self.updater.message:
                    self.updater.handle_message()
            elif event_result == win32event.WAIT_ABANDONED_0 + 1:
                # stop_event occurred
                logging.info("Request to stop service detected. Stopping service...")
                self.running = False
            else:
                # Error occurred
                logging.critical("WaitForMultipleObjects failed!")
                self.running = False


if __name__ == '__main__':
    win32serviceutil.HandleCommandLine(UpdaterServerSvc)
