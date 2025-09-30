#!/usr/bin/env python3
"""
TDD Unit Test Runner for Phase 1 and Phase 2 Optimization

This script runs unit tests with increasing difficulty levels, following TDD principles.
If the simplest tests fail, it will help identify and fix issues before proceeding.
"""

import sys
import subprocess
import logging
from pathlib import Path
from typing import List, Tuple, Dict, Any

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class TDDTestRunner:
    """Test-Driven Development test runner for optimization solvers."""
    
    def __init__(self):
        """Initialize the TDD test runner."""
        self.test_results = {}
        self.failed_tests = []
        self.passed_tests = []
        
    def run_phase1_tests(self) -> bool:
        """Run Phase 1 motion law optimization tests with increasing difficulty."""
        logger.info("🚀 STARTING PHASE 1 MOTION LAW OPTIMIZATION TESTS")
        logger.info("=" * 80)
        
        # Define test difficulty levels
        test_levels = [
            ("basic", "Basic motion law optimization"),
            ("simple", "Simple motion law optimization"),
            ("moderate", "Moderate motion law optimization"),
            ("complex", "Complex motion law optimization"),
            ("advanced", "Advanced motion law optimization")
        ]
        
        all_passed = True
        
        for level, description in test_levels:
            logger.info(f"🧪 TESTING DIFFICULTY LEVEL: {level.upper()}")
            logger.info(f"   Description: {description}")
            
            # Run specific test level
            success = self._run_specific_test("test_phase1_motion_law_unit.py", level)
            
            if success:
                logger.info(f"✅ {level.upper()} TEST PASSED")
                self.passed_tests.append(f"Phase1_{level}")
            else:
                logger.error(f"❌ {level.upper()} TEST FAILED")
                self.failed_tests.append(f"Phase1_{level}")
                all_passed = False
                
                # In TDD, if a test fails, we should stop and fix it
                logger.error("🛑 TDD PRINCIPLE: Stopping due to test failure. Fix the issue before proceeding.")
                break
            
            logger.info("-" * 60)
        
        return all_passed
    
    def run_phase2_tests(self) -> bool:
        """Run Phase 2 gear profile optimization tests with increasing difficulty."""
        logger.info("🚀 STARTING PHASE 2 GEAR PROFILE OPTIMIZATION TESTS")
        logger.info("=" * 80)
        
        # Define test difficulty levels
        test_levels = [
            ("basic", "Basic gear profile optimization"),
            ("simple", "Simple gear profile optimization"),
            ("moderate", "Moderate gear profile optimization"),
            ("complex", "Complex gear profile optimization"),
            ("advanced", "Advanced gear profile optimization")
        ]
        
        all_passed = True
        
        for level, description in test_levels:
            logger.info(f"🧪 TESTING DIFFICULTY LEVEL: {level.upper()}")
            logger.info(f"   Description: {description}")
            
            # Run specific test level
            success = self._run_specific_test("test_phase2_gear_optimization_unit.py", level)
            
            if success:
                logger.info(f"✅ {level.upper()} TEST PASSED")
                self.passed_tests.append(f"Phase2_{level}")
            else:
                logger.error(f"❌ {level.upper()} TEST FAILED")
                self.failed_tests.append(f"Phase2_{level}")
                all_passed = False
                
                # In TDD, if a test fails, we should stop and fix it
                logger.error("🛑 TDD PRINCIPLE: Stopping due to test failure. Fix the issue before proceeding.")
                break
            
            logger.info("-" * 60)
        
        return all_passed
    
    def run_integration_tests(self) -> bool:
        """Run integration tests between Phase 1 and Phase 2."""
        logger.info("🚀 STARTING INTEGRATION TESTS")
        logger.info("=" * 80)
        
        integration_tests = [
            ("test_phase1_phase2_integration", "Phase 1 + Phase 2 integration"),
            ("test_force_transfer_efficiency_optimization", "Force transfer efficiency optimization"),
            ("test_unified_constraint_satisfaction", "Unified constraint satisfaction")
        ]
        
        all_passed = True
        
        for test_name, description in integration_tests:
            logger.info(f"🧪 INTEGRATION TEST: {test_name}")
            logger.info(f"   Description: {description}")
            
            # Run specific integration test
            success = self._run_specific_test("test_phase2_gear_optimization_unit.py", test_name)
            
            if success:
                logger.info(f"✅ {test_name} PASSED")
                self.passed_tests.append(f"Integration_{test_name}")
            else:
                logger.error(f"❌ {test_name} FAILED")
                self.failed_tests.append(f"Integration_{test_name}")
                all_passed = False
                
                # In TDD, if a test fails, we should stop and fix it
                logger.error("🛑 TDD PRINCIPLE: Stopping due to test failure. Fix the issue before proceeding.")
                break
            
            logger.info("-" * 60)
        
        return all_passed
    
    def _run_specific_test(self, test_file: str, test_pattern: str) -> bool:
        """Run a specific test pattern from a test file."""
        try:
            # Construct pytest command
            cmd = [
                sys.executable, "-m", "pytest",
                f"tests/{test_file}",
                f"-k", test_pattern,
                "-v",
                "--tb=short",
                "--no-header",
                "--disable-warnings"
            ]
            
            logger.info(f"Running command: {' '.join(cmd)}")
            
            # Run the test
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=Path.cwd()
            )
            
            # Check if test passed
            success = result.returncode == 0
            
            if success:
                logger.info("Test output:")
                logger.info(result.stdout)
            else:
                logger.error("Test failed with output:")
                logger.error(result.stdout)
                logger.error("Error output:")
                logger.error(result.stderr)
            
            return success
            
        except Exception as e:
            logger.error(f"Error running test: {str(e)}")
            return False
    
    def run_all_tests(self) -> bool:
        """Run all tests following TDD principles."""
        logger.info("🚀 STARTING COMPREHENSIVE TDD TEST SUITE")
        logger.info("=" * 80)
        logger.info("Following TDD principles: If simplest tests fail, fix before proceeding")
        logger.info("=" * 80)
        
        # Phase 1 tests (motion law optimization)
        phase1_success = self.run_phase1_tests()
        
        if not phase1_success:
            logger.error("🛑 PHASE 1 TESTS FAILED - STOPPING TDD PROCESS")
            logger.error("Fix Phase 1 issues before proceeding to Phase 2")
            return False
        
        logger.info("✅ PHASE 1 TESTS ALL PASSED - PROCEEDING TO PHASE 2")
        logger.info("=" * 80)
        
        # Phase 2 tests (gear profile optimization)
        phase2_success = self.run_phase2_tests()
        
        if not phase2_success:
            logger.error("🛑 PHASE 2 TESTS FAILED - STOPPING TDD PROCESS")
            logger.error("Fix Phase 2 issues before proceeding to integration tests")
            return False
        
        logger.info("✅ PHASE 2 TESTS ALL PASSED - PROCEEDING TO INTEGRATION TESTS")
        logger.info("=" * 80)
        
        # Integration tests
        integration_success = self.run_integration_tests()
        
        if not integration_success:
            logger.error("🛑 INTEGRATION TESTS FAILED - STOPPING TDD PROCESS")
            logger.error("Fix integration issues before completing test suite")
            return False
        
        logger.info("✅ ALL TESTS PASSED - TDD PROCESS COMPLETE")
        return True
    
    def generate_test_report(self) -> str:
        """Generate a comprehensive test report."""
        report = []
        report.append("=" * 80)
        report.append("TDD TEST SUITE REPORT")
        report.append("=" * 80)
        
        report.append(f"Total Tests Passed: {len(self.passed_tests)}")
        report.append(f"Total Tests Failed: {len(self.failed_tests)}")
        report.append("")
        
        if self.passed_tests:
            report.append("✅ PASSED TESTS:")
            for test in self.passed_tests:
                report.append(f"  - {test}")
            report.append("")
        
        if self.failed_tests:
            report.append("❌ FAILED TESTS:")
            for test in self.failed_tests:
                report.append(f"  - {test}")
            report.append("")
        
        # Overall status
        if not self.failed_tests:
            report.append("🎉 ALL TESTS PASSED - SYSTEM IS READY FOR PRODUCTION")
        else:
            report.append("🛑 SOME TESTS FAILED - FIX ISSUES BEFORE PROCEEDING")
        
        report.append("=" * 80)
        
        return "\n".join(report)
    
    def run_diagnostic_tests(self) -> Dict[str, Any]:
        """Run diagnostic tests to identify potential issues."""
        logger.info("🔍 RUNNING DIAGNOSTIC TESTS")
        logger.info("=" * 80)
        
        diagnostics = {
            "casadi_available": False,
            "ipopt_available": False,
            "import_errors": [],
            "basic_functionality": False
        }
        
        # Test CasADi availability
        try:
            import casadi as ca
            diagnostics["casadi_available"] = True
            logger.info("✅ CasADi is available")
        except ImportError as e:
            diagnostics["import_errors"].append(f"CasADi import error: {str(e)}")
            logger.error("❌ CasADi is not available")
        
        # Test IPOPT availability
        if diagnostics["casadi_available"]:
            try:
                import casadi as ca
                # Try to create a simple NLP
                x = ca.SX.sym('x')
                nlp = {'x': x, 'f': x**2, 'g': x-1}
                solver = ca.nlpsol('solver', 'ipopt', nlp)
                diagnostics["ipopt_available"] = True
                logger.info("✅ IPOPT is available with CasADi")
            except Exception as e:
                diagnostics["import_errors"].append(f"IPOPT error: {str(e)}")
                logger.error("❌ IPOPT is not available with CasADi")
        
        # Test basic functionality
        try:
            from campro.optimization.collocation_optimizer import CollocationOptimizer, CollocationParameters
            from campro.optimization.phase2_gear_optimizer import Phase2GearOptimizer, Phase2Parameters
            diagnostics["basic_functionality"] = True
            logger.info("✅ Basic functionality imports work")
        except ImportError as e:
            diagnostics["import_errors"].append(f"Basic functionality import error: {str(e)}")
            logger.error("❌ Basic functionality imports failed")
        
        return diagnostics


def main():
    """Main function to run TDD test suite."""
    runner = TDDTestRunner()
    
    # Run diagnostic tests first
    logger.info("🔍 RUNNING DIAGNOSTIC TESTS FIRST")
    diagnostics = runner.run_diagnostic_tests()
    
    if diagnostics["import_errors"]:
        logger.error("🛑 IMPORT ERRORS DETECTED - FIX BEFORE PROCEEDING")
        for error in diagnostics["import_errors"]:
            logger.error(f"  - {error}")
        return False
    
    if not diagnostics["casadi_available"]:
        logger.error("🛑 CasADi is not available - install CasADi before proceeding")
        return False
    
    if not diagnostics["ipopt_available"]:
        logger.error("🛑 IPOPT is not available - install IPOPT with CasADi before proceeding")
        return False
    
    logger.info("✅ DIAGNOSTIC TESTS PASSED - PROCEEDING WITH TDD TEST SUITE")
    logger.info("=" * 80)
    
    # Run all tests
    success = runner.run_all_tests()
    
    # Generate and display report
    report = runner.generate_test_report()
    print("\n" + report)
    
    # Save report to file
    report_path = Path("test_results/tdd_test_report.txt")
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, 'w') as f:
        f.write(report)
    
    logger.info(f"📊 Test report saved to: {report_path}")
    
    return success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
