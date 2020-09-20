import unittest.mock
from unittest import TestCase
from unittest.mock import MagicMock, Mock, patch

import serial
from pyexpect import expect

from mariner.exceptions import UnexpectedResponse
from mariner.mars import ElegooMars, PrinterState


class ElegooMarsTest(TestCase):
    printer: ElegooMars
    serial_port_patcher: unittest.mock._patch
    serial_port_mock: MagicMock

    def setUp(self) -> None:
        self.serial_port_mock = Mock(spec=serial.Serial)
        self.serial_port_patcher = patch("mariner.mars.serial.Serial")
        serial_port_constructor = self.serial_port_patcher.start()
        serial_port_constructor.return_value = self.serial_port_mock
        self.printer = ElegooMars()

    def tearDown(self) -> None:
        self.serial_port_patcher.stop()

    def test_open_and_close(self) -> None:
        self.serial_port_mock.open.assert_not_called()
        self.serial_port_mock.close.assert_not_called()

        self.printer.open()
        self.serial_port_mock.open.assert_called_once_with()
        self.serial_port_mock.close.assert_not_called()
        self.serial_port_mock.reset_mock()

        self.printer.close()
        self.serial_port_mock.open.assert_not_called()
        self.serial_port_mock.close.assert_called_once_with()

    def test_usage_with_context_manager(self) -> None:
        self.serial_port_mock.open.assert_not_called()
        self.serial_port_mock.close.assert_not_called()

        with self.printer:
            self.serial_port_mock.open.assert_called_once_with()
            self.serial_port_mock.close.assert_not_called()
            self.serial_port_mock.reset_mock()

        self.serial_port_mock.open.assert_not_called()
        self.serial_port_mock.close.assert_called_once_with()

    def test_get_firmware_version(self) -> None:
        self.serial_port_mock.readline.return_value = b"ok V4.3.4_LCDC\n"

        self.printer.open()
        firmware_version = self.printer.get_firmware_version()
        self.printer.close()

        self.serial_port_mock.write.assert_called_once_with(b"M4002")
        expect(firmware_version).to_equal("V4.3.4_LCDC")

    def test_get_state(self) -> None:
        self.serial_port_mock.readline.return_value = (
            b"ok B:0/0 X:0.000 Y:0.000 Z:151.900 F:0/0 D:31540/0/1 "
        )

        self.printer.open()
        # TODO: make this return a dataclass with the parsed information
        self.printer.get_state()
        self.printer.close()

        self.serial_port_mock.write.assert_called_once_with(b"M4000")

    def test_get_print_status_when_not_printing(self) -> None:
        self.serial_port_mock.readline.return_value = (
            b"Error:It's not printing now!\r\nok N:0\r\n"
        )

        self.printer.open()
        print_status = self.printer.get_print_status()
        self.printer.close()

        self.serial_port_mock.write.assert_called_once_with(b"M27")
        expect(print_status.state).to_equal(PrinterState.IDLE)
        expect(print_status.current_byte).to_be_none()
        expect(print_status.total_bytes).to_be_none()

    def test_get_print_status_while_starting_print(self) -> None:
        self.serial_port_mock.readline.return_value = (
            b"SD printing byte 0/23543968\r\nok N:0\r\n"
        )

        self.printer.open()
        print_status = self.printer.get_print_status()
        self.printer.close()

        self.serial_port_mock.write.assert_called_once_with(b"M27")
        expect(print_status.state).to_equal(PrinterState.STARTING_PRINT)
        expect(print_status.current_byte).to_equal(0)
        expect(print_status.total_bytes).to_equal(23543968)

    def test_get_print_status_while_printing(self) -> None:
        self.serial_port_mock.readline.return_value = (
            b"SD printing byte 23012/23543968\r\nok N:0\r\n"
        )

        self.printer.open()
        print_status = self.printer.get_print_status()
        self.printer.close()

        self.serial_port_mock.write.assert_called_once_with(b"M27")
        expect(print_status.state).to_equal(PrinterState.PRINTING)
        expect(print_status.current_byte).to_equal(23012)
        expect(print_status.total_bytes).to_equal(23543968)

    def test_get_z_pos(self) -> None:
        self.serial_port_mock.readline.return_value = (
            b"ok C: X:0.000000 Y:0.000000 Z:155.000000 E:0.000000\r\n"
        )

        self.printer.open()
        z_pos = self.printer.get_z_pos()
        self.printer.close()

        self.serial_port_mock.write.assert_called_once_with(b"M114")
        expect(z_pos).is_almost_equal(155.0, max_delta=1e-9)

    def test_get_selected_file(self) -> None:
        self.serial_port_mock.readline.return_value = b"ok 'LittleBBC.ctb'\r\n"

        self.printer.open()
        selected_file = self.printer.get_selected_file()
        self.printer.close()

        self.serial_port_mock.write.assert_called_once_with(b"M4006")
        expect(selected_file).equals("LittleBBC.ctb")

    def test_select_file(self) -> None:
        self.serial_port_mock.readline.return_value = (
            # FIXME: this isn't right, readline would return only the first one
            b"File opened:lattice.ctb Size:26058253\r\nFile selected\r\nok N:0\r\n"
        )
        self.printer.open()
        self.printer.select_file("lattice.ctb")
        self.printer.close()
        self.serial_port_mock.write.assert_called_once_with(b"M23 lattice.ctb")

    def test_select_nonexisting_file(self) -> None:
        self.serial_port_mock.readline.return_value = (
            # FIXME: this isn't right, readline would return only the first one
            b"//############Error!cann't open file foobar.ctb!\r\n"
            + b"open failed, File :foobar.ctb\r\n"
            + b"ok N:0\r\n"
        )
        self.printer.open()
        with self.assertRaises(UnexpectedResponse):
            self.printer.select_file("foobar.ctb")
        self.printer.close()
        self.serial_port_mock.write.assert_called_once_with(b"M23 foobar.ctb")

    def test_stop_printing(self) -> None:
        self.serial_port_mock.readline.return_value = b"ok N:0\r\n"
        self.printer.open()
        self.printer.stop_printing()
        self.serial_port_mock.write.assert_called_once_with(b"M33")
        self.printer.close()

    def test_stop_printing_when_not_printing(self) -> None:
        self.serial_port_mock.readline.return_value = (
            # FIXME: this isn't right, readline would return only the first one
            b"Error:It's not printing now!\r\nok N:0\r\n"
        )
        self.printer.open()
        with self.assertRaises(UnexpectedResponse):
            self.printer.stop_printing()
        self.printer.close()
        self.serial_port_mock.write.assert_called_once_with(b"M33")

    def test_start_printing(self) -> None:
        self.serial_port_mock.readline.return_value = b"ok N:0\r\n"
        self.printer.open()
        self.printer.start_printing("benchy.ctb")
        self.serial_port_mock.write.assert_called_once_with(b"M6030 'benchy.ctb'")
        self.printer.close()

    def test_start_printing_with_invalid_response(self) -> None:
        self.serial_port_mock.readline.return_value = b"foobar\r\n"
        self.printer.open()
        with self.assertRaises(UnexpectedResponse):
            self.printer.start_printing("benchy.ctb")
        self.serial_port_mock.write.assert_called_once_with(b"M6030 'benchy.ctb'")
        self.printer.close()

    def test_resume_printing(self) -> None:
        self.serial_port_mock.readline.return_value = b"ok N:0\r\n"
        self.printer.open()
        self.printer.resume_printing()
        self.serial_port_mock.write.assert_called_once_with(b"M24")
        self.printer.close()

    def test_pause_printing(self) -> None:
        self.serial_port_mock.readline.return_value = b"ok N:0\r\n"
        self.printer.open()
        self.printer.pause_printing()
        self.serial_port_mock.write.assert_called_once_with(b"M25")
        self.printer.close()

    def test_move_by(self) -> None:
        self.serial_port_mock.readline.return_value = b"ok N:0\r\n"
        self.printer.open()

        self.printer.move_by(10)
        self.serial_port_mock.write.assert_called_once_with(b"G0 Z10.0 F600 I0")
        self.serial_port_mock.reset_mock()

        self.printer.move_by(-10)
        self.serial_port_mock.write.assert_called_once_with(b"G0 Z-10.0 F600 I0")
        self.serial_port_mock.reset_mock()

        self.printer.move_by(15.3, mm_per_min=30)
        self.serial_port_mock.write.assert_called_once_with(b"G0 Z15.3 F30 I0")
        self.serial_port_mock.reset_mock()

        self.printer.close()

    def test_move_to_home(self) -> None:
        self.serial_port_mock.readline.return_value = b"ok N:0\r\n"
        self.printer.open()
        self.printer.move_to_home()
        self.serial_port_mock.write.assert_called_once_with(b"G28")
        self.printer.close()

    def test_stop_motors(self) -> None:
        self.serial_port_mock.readline.return_value = b"ok N:0\r\n"
        self.printer.open()
        self.printer.stop_motors()
        self.serial_port_mock.write.assert_called_once_with(b"M112")
        self.printer.close()

    def test_reboot(self) -> None:
        self.printer.open()

        self.printer.reboot()
        self.serial_port_mock.write.assert_called_once_with(b"M6040 I0")
        self.serial_port_mock.reset_mock()

        self.printer.reboot(delay_in_ms=123)
        self.serial_port_mock.write.assert_called_once_with(b"M6040 I123")

        self.printer.close()
