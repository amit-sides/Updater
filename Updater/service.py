import win32serviceutil
import win32service
import win32event
import win32file
import servicemanager
import logging

from Updater import settings
from Updater import registry
from Updater import updater


class UpdaterServerSvc(win32serviceutil.ServiceFramework):
    _svc_name_ = f"{settings.SOFTWARE_NAME}Updater"
    _svc_display_name_ = f"{settings.SOFTWARE_NAME} Updater"
    _svc_description_ = f"Updates the program {settings.SOFTWARE_NAME}"

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

    @staticmethod
    def init_registry():
        if not registry.exists(settings.REGISTRY_PATH):
            registry.create_key(settings.REGISTRY_PATH)
        if not registry.exists(settings.AUTO_INSTALLATIONS_REGISTRY):
            registry.set_value(settings.AUTO_INSTALLATIONS_REGISTRY, settings.AUTO_INSTALLATIONS)
        if not registry.exists(settings.UPDATING_SERVER_REGISTRY):
            registry.set_value(settings.UPDATING_SERVER_REGISTRY, settings.UPDATING_SERVER)
        if not registry.exists(settings.PORT_REGISTRY):
            registry.set_value(settings.PORT_REGISTRY, settings.PORT)
        if not registry.exists(settings.RSA_MODULO_REGISTRY):
            registry.set_value(settings.RSA_MODULO_REGISTRY, settings.RSA_MODULO)
        if not registry.exists(settings.RSA_PUBLIC_REGISTRY):
            registry.set_value(settings.RSA_PUBLIC_REGISTRY, settings.PUBLIC_KEY)
        if not registry.exists(settings.UPDATE_MAJOR_REGISTRY):
            registry.set_value(settings.UPDATE_MAJOR_REGISTRY, settings.UPDATE_MAJOR)
        if not registry.exists(settings.UPDATE_MINOR_REGISTRY):
            registry.set_value(settings.UPDATE_MINOR_REGISTRY, settings.UPDATE_MINOR)
        if not registry.exists(settings.VERSION_MAJOR_REGISTRY):
            registry.set_value(settings.VERSION_MAJOR_REGISTRY, settings.VERSION_MAJOR)
        if not registry.exists(settings.VERSION_MINOR_REGISTRY):
            registry.set_value(settings.VERSION_MINOR_REGISTRY, settings.VERSION_MINOR)
        if not registry.exists(settings.ADDRESS_ID_REGISTRY):
            registry.set_value(settings.ADDRESS_ID_REGISTRY, settings.ADDRESS_ID)

    @staticmethod
    def init():
        # Assumes all file are placed correctly at settings.SOFTWARE_PATH
        settings.init_settings()

        UpdaterServerSvc.init_registry()
        pass

    def run(self):
        # Setup the logger
        self.setup_logger()

        # Initializes the service
        self.init()

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