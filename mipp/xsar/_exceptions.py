class SatReaderError(Exception):
    pass
class CalibrationError(SatReaderError):
    pass
class SatNoFiles(SatReaderError):
    pass
