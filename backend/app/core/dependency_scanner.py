"""
Dependency vulnerability scanner for ISP Framework.

Provides automated security scanning of Python dependencies.
"""

import json
import os
import subprocess
from datetime import datetime, timezone
from typing import Dict, List, Tuple

import structlog

from app.core.observability import log_audit_event

logger = structlog.get_logger("isp.security.scanner")


class DependencyScanner:
    """Scans Python dependencies for security vulnerabilities."""

    def __init__(self, requirements_file: str = None):
        self.requirements_file = requirements_file or "requirements.txt"
        self.scan_results = {}
        self.last_scan = None

    def run_bandit_scan(self, target_dir: str = "app") -> Dict:
        """Run Bandit static analysis security scanner."""
        try:
            cmd = [
                "bandit",
                "-r",
                target_dir,
                "-f",
                "json",
                "-ll",  # Only show medium and high severity
                "--skip",
                "B101,B601",  # Skip assert and shell injection (common false positives)
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            )

            if result.returncode == 0:
                scan_data = json.loads(result.stdout) if result.stdout else {}
            else:
                # Bandit returns non-zero when issues are found
                scan_data = json.loads(result.stdout) if result.stdout else {}

            issues = scan_data.get("results", [])

            # Categorize issues by severity
            categorized = {"high": [], "medium": [], "low": []}

            for issue in issues:
                severity = issue.get("issue_severity", "UNDEFINED").lower()
                if severity in categorized:
                    categorized[severity].append(
                        {
                            "test_id": issue.get("test_id"),
                            "test_name": issue.get("test_name"),
                            "filename": issue.get("filename"),
                            "line_number": issue.get("line_number"),
                            "issue_text": issue.get("issue_text"),
                            "confidence": issue.get("issue_confidence"),
                        }
                    )

            scan_result = {
                "tool": "bandit",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "total_issues": len(issues),
                "issues_by_severity": categorized,
                "scan_successful": True,
            }

            log_audit_event(
                domain="security",
                event="bandit_scan_completed",
                total_issues=len(issues),
                high_severity=len(categorized["high"]),
                medium_severity=len(categorized["medium"]),
            )

            return scan_result

        except FileNotFoundError:
            logger.error("Bandit not found - install with: pip install bandit")
            return {
                "tool": "bandit",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "error": "Bandit not installed",
                "scan_successful": False,
            }
        except Exception as e:
            logger.error("Bandit scan failed", error=str(e))
            return {
                "tool": "bandit",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "error": str(e),
                "scan_successful": False,
            }

    def run_safety_scan(self) -> Dict:
        """Run Safety vulnerability scanner for dependencies."""
        try:
            cmd = ["safety", "check", "--json", "--file", self.requirements_file]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            )

            if result.returncode == 0:
                # No vulnerabilities found
                vulnerabilities = []
            else:
                # Parse vulnerabilities from output
                try:
                    vulnerabilities = json.loads(result.stdout)
                except json.JSONDecodeError:
                    # Fallback to parsing text output
                    vulnerabilities = self._parse_safety_text_output(result.stdout)

            # Categorize vulnerabilities
            categorized = {"critical": [], "high": [], "medium": [], "low": []}

            for vuln in vulnerabilities:
                # Safety doesn't provide severity, so we estimate based on CVE score
                severity = self._estimate_severity(vuln)
                categorized[severity].append(
                    {
                        "package": vuln.get("package"),
                        "installed_version": vuln.get("installed_version"),
                        "vulnerability_id": vuln.get("vulnerability_id"),
                        "advisory": vuln.get("advisory"),
                        "more_info_url": vuln.get("more_info_url"),
                    }
                )

            scan_result = {
                "tool": "safety",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "total_vulnerabilities": len(vulnerabilities),
                "vulnerabilities_by_severity": categorized,
                "scan_successful": True,
            }

            log_audit_event(
                domain="security",
                event="safety_scan_completed",
                total_vulnerabilities=len(vulnerabilities),
                critical=len(categorized["critical"]),
                high=len(categorized["high"]),
            )

            return scan_result

        except FileNotFoundError:
            logger.error("Safety not found - install with: pip install safety")
            return {
                "tool": "safety",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "error": "Safety not installed",
                "scan_successful": False,
            }
        except Exception as e:
            logger.error("Safety scan failed", error=str(e))
            return {
                "tool": "safety",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "error": str(e),
                "scan_successful": False,
            }

    def _parse_safety_text_output(self, output: str) -> List[Dict]:
        """Parse Safety text output when JSON parsing fails."""
        vulnerabilities = []
        lines = output.strip().split("\n")

        current_vuln = {}
        for line in lines:
            line = line.strip()
            if line.startswith("-> "):
                # New vulnerability
                if current_vuln:
                    vulnerabilities.append(current_vuln)
                current_vuln = {"advisory": line[3:]}
            elif " installed: " in line:
                parts = line.split(" installed: ")
                current_vuln["package"] = parts[0]
                current_vuln["installed_version"] = parts[1]

        if current_vuln:
            vulnerabilities.append(current_vuln)

        return vulnerabilities

    def _estimate_severity(self, vulnerability: Dict) -> str:
        """Estimate vulnerability severity based on available information."""
        advisory = vulnerability.get("advisory", "").lower()

        # Keywords that indicate high severity
        high_keywords = ["remote code execution", "rce", "sql injection", "xss", "csrf"]
        critical_keywords = ["critical", "remote shell", "arbitrary code"]

        if any(keyword in advisory for keyword in critical_keywords):
            return "critical"
        elif any(keyword in advisory for keyword in high_keywords):
            return "high"
        elif "denial of service" in advisory or "dos" in advisory:
            return "medium"
        else:
            return "low"

    def run_pip_audit(self) -> Dict:
        """Run pip-audit for dependency vulnerability scanning."""
        try:
            cmd = [
                "pip-audit",
                "--format=json",
                "--requirement",
                self.requirements_file,
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            )

            if result.returncode == 0:
                audit_data = json.loads(result.stdout) if result.stdout else {}
            else:
                audit_data = json.loads(result.stdout) if result.stdout else {}

            vulnerabilities = audit_data.get("vulnerabilities", [])

            # Categorize by severity
            categorized = {"critical": [], "high": [], "medium": [], "low": []}

            for vuln in vulnerabilities:
                severity = vuln.get("severity", "unknown").lower()
                if severity not in categorized:
                    severity = "medium"  # Default for unknown severity

                categorized[severity].append(
                    {
                        "package": vuln.get("package"),
                        "installed_version": vuln.get("installed_version"),
                        "fixed_version": vuln.get("fixed_version"),
                        "vulnerability_id": vuln.get("id"),
                        "description": vuln.get("description"),
                        "severity": vuln.get("severity"),
                    }
                )

            scan_result = {
                "tool": "pip-audit",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "total_vulnerabilities": len(vulnerabilities),
                "vulnerabilities_by_severity": categorized,
                "scan_successful": True,
            }

            return scan_result

        except FileNotFoundError:
            logger.warning("pip-audit not found - install with: pip install pip-audit")
            return {
                "tool": "pip-audit",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "error": "pip-audit not installed",
                "scan_successful": False,
            }
        except Exception as e:
            logger.error("pip-audit scan failed", error=str(e))
            return {
                "tool": "pip-audit",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "error": str(e),
                "scan_successful": False,
            }

    def run_comprehensive_scan(self) -> Dict:
        """Run all available security scanners."""
        logger.info("Starting comprehensive security scan")

        results = {
            "scan_timestamp": datetime.now(timezone.utc).isoformat(),
            "scanners": {},
        }

        # Run Bandit (static analysis)
        results["scanners"]["bandit"] = self.run_bandit_scan()

        # Run Safety (dependency vulnerabilities)
        results["scanners"]["safety"] = self.run_safety_scan()

        # Run pip-audit (alternative dependency scanner)
        results["scanners"]["pip_audit"] = self.run_pip_audit()

        # Calculate overall summary
        total_issues = 0
        total_vulnerabilities = 0
        critical_count = 0
        high_count = 0

        for scanner_name, scanner_result in results["scanners"].items():
            if scanner_result.get("scan_successful"):
                if "total_issues" in scanner_result:
                    total_issues += scanner_result["total_issues"]
                    issues_by_severity = scanner_result.get("issues_by_severity", {})
                    critical_count += len(
                        issues_by_severity.get("high", [])
                    )  # Bandit high = critical
                    high_count += len(issues_by_severity.get("medium", []))

                if "total_vulnerabilities" in scanner_result:
                    total_vulnerabilities += scanner_result["total_vulnerabilities"]
                    vulns_by_severity = scanner_result.get(
                        "vulnerabilities_by_severity", {}
                    )
                    critical_count += len(vulns_by_severity.get("critical", []))
                    high_count += len(vulns_by_severity.get("high", []))

        results["summary"] = {
            "total_issues": total_issues,
            "total_vulnerabilities": total_vulnerabilities,
            "critical_count": critical_count,
            "high_count": high_count,
            "scan_successful": any(
                r.get("scan_successful") for r in results["scanners"].values()
            ),
        }

        self.scan_results = results
        self.last_scan = datetime.now(timezone.utc)

        log_audit_event(
            domain="security",
            event="comprehensive_scan_completed",
            total_issues=total_issues,
            total_vulnerabilities=total_vulnerabilities,
            critical_count=critical_count,
            high_count=high_count,
        )

        logger.info(
            "Comprehensive security scan completed",
            total_issues=total_issues,
            total_vulnerabilities=total_vulnerabilities,
            critical_count=critical_count,
            high_count=high_count,
        )

        return results

    def get_scan_summary(self) -> Dict:
        """Get a summary of the last scan results."""
        if not self.scan_results:
            return {"error": "No scan results available"}

        return {
            "last_scan": self.last_scan.isoformat() if self.last_scan else None,
            "summary": self.scan_results.get("summary", {}),
            "scanners_status": {
                name: result.get("scan_successful", False)
                for name, result in self.scan_results.get("scanners", {}).items()
            },
        }


# Global scanner instance
dependency_scanner = DependencyScanner()


def run_security_scan() -> Dict:
    """Run comprehensive security scan."""
    return dependency_scanner.run_comprehensive_scan()


def get_security_scan_summary() -> Dict:
    """Get summary of last security scan."""
    return dependency_scanner.get_scan_summary()


def check_security_requirements() -> Tuple[bool, List[str]]:
    """Check if security scanning tools are installed."""
    missing_tools = []

    tools = ["bandit", "safety", "pip-audit"]
    for tool in tools:
        try:
            subprocess.run([tool, "--version"], capture_output=True, check=True)
        except (FileNotFoundError, subprocess.CalledProcessError):
            missing_tools.append(tool)

    return len(missing_tools) == 0, missing_tools
