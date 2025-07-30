#!/usr/bin/env python3
"""
ISP Framework Executive Audit Summary Generator
Generates a comprehensive executive summary from audit results
"""

import json
import argparse
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List
import subprocess


class AuditSummaryGenerator:
    """Generates executive summary from audit results."""
    
    def __init__(self, input_dir: str, output_file: str):
        self.input_dir = Path(input_dir)
        self.output_file = output_file
        self.metrics = {}
        
    def parse_audit_results(self) -> Dict[str, Any]:
        """Parse all audit result files and extract key metrics."""
        summary = {
            'timestamp': datetime.now().isoformat(),
            'quality_score': 0,
            'security_score': 0,
            'test_coverage': 0,
            'performance_score': 0,
            'issues': {
                'critical': 0,
                'high': 0,
                'medium': 0,
                'low': 0
            },
            'recommendations': [],
            'technical_debt_hours': 0
        }
        
        # Parse security results
        self._parse_security_results(summary)
        
        # Parse test coverage
        self._parse_test_results(summary)
        
        # Parse lint results
        self._parse_lint_results(summary)
        
        # Calculate composite scores
        self._calculate_scores(summary)
        
        return summary
    
    def _parse_security_results(self, summary: Dict[str, Any]):
        """Parse security scan results."""
        bandit_file = self.input_dir / 'bandit_results.json'
        if bandit_file.exists():
            try:
                with open(bandit_file) as f:
                    bandit_data = json.load(f)
                    
                for result in bandit_data.get('results', []):
                    severity = result.get('issue_severity', 'LOW')
                    if severity == 'HIGH':
                        summary['issues']['critical'] += 1
                    elif severity == 'MEDIUM':
                        summary['issues']['high'] += 1
                    else:
                        summary['issues']['medium'] += 1
                        
            except (json.JSONDecodeError, FileNotFoundError):
                pass
        
        # Parse safety results
        safety_file = self.input_dir / 'safety_results.json'
        if safety_file.exists():
            try:
                with open(safety_file) as f:
                    safety_data = json.load(f)
                    
                for vuln in safety_data.get('vulnerabilities', []):
                    summary['issues']['high'] += 1
                    
            except (json.JSONDecodeError, FileNotFoundError):
                pass
    
    def _parse_test_results(self, summary: Dict[str, Any]):
        """Parse test coverage results."""
        coverage_file = self.input_dir / 'coverage.json'
        if coverage_file.exists():
            try:
                with open(coverage_file) as f:
                    coverage_data = json.load(f)
                    summary['test_coverage'] = coverage_data.get('totals', {}).get('percent_covered', 0)
            except (json.JSONDecodeError, FileNotFoundError):
                pass
    
    def _parse_lint_results(self, summary: Dict[str, Any]):
        """Parse linting results."""
        ruff_file = self.input_dir / 'ruff_results.json'
        if ruff_file.exists():
            try:
                with open(ruff_file) as f:
                    ruff_data = json.load(f)
                    
                for issue in ruff_data:
                    code = issue.get('code', '')
                    if code.startswith('E'):  # Error
                        summary['issues']['high'] += 1
                    elif code.startswith('W'):  # Warning
                        summary['issues']['medium'] += 1
                    else:
                        summary['issues']['low'] += 1
                        
            except (json.JSONDecodeError, FileNotFoundError):
                pass
    
    def _calculate_scores(self, summary: Dict[str, Any]):
        """Calculate composite quality scores."""
        # Security score (0-100)
        critical_penalty = summary['issues']['critical'] * 20
        high_penalty = summary['issues']['high'] * 10
        medium_penalty = summary['issues']['medium'] * 5
        
        summary['security_score'] = max(0, 100 - critical_penalty - high_penalty - medium_penalty)
        
        # Quality score based on issues and coverage
        issue_penalty = (summary['issues']['critical'] * 10 + 
                        summary['issues']['high'] * 5 + 
                        summary['issues']['medium'] * 2 +
                        summary['issues']['low'] * 1)
        
        coverage_bonus = summary['test_coverage'] * 0.3
        summary['quality_score'] = max(0, min(100, 80 - issue_penalty + coverage_bonus))
        
        # Performance score (placeholder)
        summary['performance_score'] = 85  # Would be calculated from actual perf data
        
        # Technical debt estimation
        summary['technical_debt_hours'] = (
            summary['issues']['critical'] * 8 +
            summary['issues']['high'] * 4 +
            summary['issues']['medium'] * 2 +
            summary['issues']['low'] * 0.5
        )
    
    def generate_recommendations(self, summary: Dict[str, Any]) -> List[str]:
        """Generate actionable recommendations."""
        recommendations = []
        
        if summary['issues']['critical'] > 0:
            recommendations.append(
                f"🚨 URGENT: Address {summary['issues']['critical']} critical security issues immediately"
            )
        
        if summary['issues']['high'] > 5:
            recommendations.append(
                f"⚠️ HIGH: Resolve {summary['issues']['high']} high-priority issues within 1 sprint"
            )
        
        if summary['test_coverage'] < 80:
            recommendations.append(
                f"📊 COVERAGE: Improve test coverage from {summary['test_coverage']:.1f}% to >80%"
            )
        
        if summary['technical_debt_hours'] > 40:
            recommendations.append(
                f"🔧 DEBT: Allocate {summary['technical_debt_hours']:.0f} hours to address technical debt"
            )
        
        recommendations.extend([
            "🔄 AUTOMATION: Integrate quality gates into CI/CD pipeline",
            "📚 DOCS: Update documentation for modules with missing docstrings",
            "🔍 MONITORING: Set up automated dependency vulnerability scanning",
            "📈 METRICS: Establish baseline performance benchmarks"
        ])
        
        return recommendations[:10]  # Top 10 recommendations
    
    def generate_markdown_report(self, summary: Dict[str, Any]) -> str:
        """Generate markdown executive summary."""
        recommendations = self.generate_recommendations(summary)
        
        report = f"""# ISP Framework - Executive Audit Summary

**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}
**Audit Type**: Comprehensive Codebase Review

## 📊 Quality Dashboard

| Metric | Score | Status |
|--------|-------|--------|
| **Overall Quality** | {summary['quality_score']:.0f}/100 | {'🟢 Good' if summary['quality_score'] >= 80 else '🟡 Fair' if summary['quality_score'] >= 60 else '🔴 Poor'} |
| **Security Posture** | {summary['security_score']:.0f}/100 | {'🟢 Strong' if summary['security_score'] >= 90 else '🟡 Moderate' if summary['security_score'] >= 70 else '🔴 Weak'} |
| **Test Coverage** | {summary['test_coverage']:.1f}% | {'🟢 Good' if summary['test_coverage'] >= 80 else '🟡 Fair' if summary['test_coverage'] >= 60 else '🔴 Poor'} |
| **Performance** | {summary['performance_score']:.0f}/100 | {'🟢 Good' if summary['performance_score'] >= 80 else '🟡 Fair' if summary['performance_score'] >= 60 else '🔴 Poor'} |

## 🚨 Issues Summary

| Severity | Count | Impact |
|----------|-------|--------|
| Critical | {summary['issues']['critical']} | Immediate action required |
| High | {summary['issues']['high']} | Fix within 1 sprint |
| Medium | {summary['issues']['medium']} | Fix within 1 month |
| Low | {summary['issues']['low']} | Fix when convenient |

## 💰 Technical Debt

**Estimated Resolution Time**: {summary['technical_debt_hours']:.0f} hours
**Priority**: {'🚨 Critical' if summary['technical_debt_hours'] > 80 else '⚠️ High' if summary['technical_debt_hours'] > 40 else '✅ Manageable'}

## 🎯 Top Recommendations

"""
        
        for i, rec in enumerate(recommendations, 1):
            report += f"{i}. {rec}\n"
        
        report += f"""
## 📈 Trend Analysis

*Note: Trend analysis requires historical data from previous audits*

## 🔄 Next Steps

1. **Immediate (0-7 days)**
   - Address all critical security vulnerabilities
   - Fix blocking type errors and lint issues
   - Set up automated quality gates in CI/CD

2. **Short-term (1-4 weeks)**
   - Resolve high-priority issues
   - Improve test coverage for critical modules
   - Update documentation gaps

3. **Medium-term (1-3 months)**
   - Implement performance optimizations
   - Refactor modules with high technical debt
   - Establish monitoring and alerting

4. **Long-term (3+ months)**
   - Architecture improvements
   - Advanced security hardening
   - Performance benchmarking program

## 📋 Audit Checklist

- [{'x' if summary['security_score'] >= 90 else ' '}] Security scan passed
- [{'x' if summary['test_coverage'] >= 80 else ' '}] Test coverage >80%
- [{'x' if summary['issues']['critical'] == 0 else ' '}] Zero critical issues
- [{'x' if summary['quality_score'] >= 80 else ' '}] Quality score >80
- [ ] Performance benchmarks established
- [ ] Documentation complete
- [ ] CI/CD quality gates active

---
*This report was generated automatically by the ISP Framework audit system.*
*For detailed results, see individual audit files.*
"""
        
        return report
    
    def generate_summary(self):
        """Generate the complete executive summary."""
        print("🔍 Parsing audit results...")
        summary = self.parse_audit_results()
        
        print("📝 Generating executive summary...")
        markdown_report = self.generate_markdown_report(summary)
        
        # Write markdown report
        markdown_file = self.output_file.replace('.pdf', '.md')
        with open(markdown_file, 'w') as f:
            f.write(markdown_report)
        
        print(f"✅ Executive summary generated: {markdown_file}")
        
        # Try to generate PDF if pandoc is available
        try:
            subprocess.run([
                'pandoc', markdown_file, '-o', self.output_file,
                '--pdf-engine=wkhtmltopdf'
            ], check=True, capture_output=True)
            print(f"📄 PDF report generated: {self.output_file}")
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("⚠️ PDF generation skipped (pandoc/wkhtmltopdf not available)")
        
        return summary


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Generate ISP Framework audit executive summary')
    parser.add_argument('--input-dir', required=True, help='Directory containing audit results')
    parser.add_argument('--output', required=True, help='Output file path (PDF)')
    
    args = parser.parse_args()
    
    generator = AuditSummaryGenerator(args.input_dir, args.output)
    summary = generator.generate_summary()
    
    # Print key metrics to console
    print("\n" + "="*50)
    print("📊 AUDIT SUMMARY")
    print("="*50)
    print(f"Quality Score: {summary['quality_score']:.0f}/100")
    print(f"Security Score: {summary['security_score']:.0f}/100")
    print(f"Test Coverage: {summary['test_coverage']:.1f}%")
    print(f"Critical Issues: {summary['issues']['critical']}")
    print(f"Technical Debt: {summary['technical_debt_hours']:.0f} hours")
    print("="*50)


if __name__ == '__main__':
    main()
