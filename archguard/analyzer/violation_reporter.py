from archguard import dto, protocols


class ViolationReporter(protocols.ViolationReporterProtocol):
    def format(self, scan_result: dto.ScanResult) -> str:
        header = f"{len(scan_result.violations)} violations\n\n"
        
        for violation in scan_result.violations:
            
