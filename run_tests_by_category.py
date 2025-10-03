#!/usr/bin/env python3
"""
CamProV5 Test Runner by Category

This script provides a comprehensive test runner that can execute tests by category
or run all tests with the new organized structure.
"""

import sys
import subprocess
import logging
from pathlib import Path
from typing import List
import argparse

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class CategoryTestRunner:
    """Test runner for organized test categories."""
    
    def __init__(self):
        """Initialize the category test runner."""
        self.test_categories = {
            'physics': {
                'path': 'tests/physics/',
                'description': 'Physics calculations and force transfer analysis',
                'files': [
                    'test_physics_calculations.py',
                    'test_force_transfer_analyzer.py',
                    'test_extracted_physics.py',
                    'test_litvin_physics.py'
                ]
            },
            'optimization': {
                'path': 'tests/optimization/',
                'description': 'Optimization algorithms and solvers',
                'files': [
                    'test_collocation_gear_optimizer.py',
                    'test_efficiency_optimizer.py',
                    'test_litvin_optimizer.py',
                    'test_efficiency_comparison.py'
                ]
            },
            'phases': {
                'path': 'tests/phases/',
                'description': 'Phase-specific optimization tests',
                'files': [
                    'test_phase1_motion_law_unit.py',
                    'test_phase2_gear_optimization_unit.py',
                    'test_phase2_backcompat_fixed_ratio.py',
                    'test_phase2_global_ratio.py',
                    'test_phase2_r_no_slip.py',
                    'test_piecewise_initial_guess.py',
                    'test_simplified_models_replacement.py'
                ]
            },
            'integration': {
                'path': 'tests/integration/',
                'description': 'Integration and end-to-end tests',
                'files': [
                    'test_pipeline_integration.py',
                    'test_unified_pipeline.py',
                    'test_kotlin_integration.py',
                    'test_python_bridge_roundtrip.py',
                    'test_unified_pipeline_backcompat_ratio.py'
                ]
            },
            'ui': {
                'path': 'tests/ui/',
                'description': 'User interface component tests',
                'files': [
                    'test_ui_components.py'
                ]
            },
            'fea': {
                'path': 'tests/fea/',
                'description': 'Finite Element Analysis tests',
                'files': [
                    'test_fea_analyzer.py',
                    'test_rust_engine_wrapper.py'
                ]
            },
            'gear_generation': {
                'path': 'tests/gear_generation/',
                'description': 'Gear profile generation tests',
                'files': [
                    'test_extracted_gear_generation.py',
                    'test_profile_generator_uses_r_inst.py',
                    'test_tooth_generator.py'
                ]
            },
            'collocation': {
                'path': 'tests/collocation/',
                'description': 'Collocation method tests',
                'files': [
                    'test_extracted_collocation.py',
                    'test_collocation_constraint_relaxation.py',
                    'test_discretization_periodic_nodes.py',
                    'test_constraint_relaxation_improved.py'
                ]
            },
            'robust_design': {
                'path': 'tests/robust_design/',
                'description': 'Robust design and TDD tests',
                'files': [
                    'test_robust_gear_design.py',
                    'test_robust_gear_design_tdd.py'
                ]
            },
            'cli_pipeline': {
                'path': 'tests/cli_pipeline/',
                'description': 'CLI and pipeline tests',
                'files': [
                    'test_cli_placeholder_fallback.py',
                    'test_pipeline_cli.py'
                ]
            }
        }
        
        self.results = {}
    
    def list_categories(self) -> None:
        """List all available test categories."""
        logger.info("Available Test Categories:")
        logger.info("=" * 50)
        for category, info in self.test_categories.items():
            logger.info(f"{category:15} - {info['description']}")
            logger.info(f"{'':15}   Path: {info['path']}")
            logger.info(f"{'':15}   Files: {len(info['files'])}")
            logger.info("")  # Empty line
    
    def run_category(self, category: str, verbose: bool = False) -> bool:
        """Run tests for a specific category."""
        if category not in self.test_categories:
            logger.error(f"Unknown category: {category}")
            logger.info("Available categories:")
            for cat in self.test_categories.keys():
                logger.info(f"  - {cat}")
            return False
        
        category_info = self.test_categories[category]
        logger.info(f"Running {category} tests...")
        logger.info(f"Description: {category_info['description']}")
        logger.info(f"Path: {category_info['path']}")
        
        # Check if category directory exists
        category_path = Path(category_info['path'])
        if not category_path.exists():
            logger.error(f"Category path does not exist: {category_path}")
            return False
        
        # Run pytest on the category directory
        cmd = [sys.executable, "-m", "pytest", category_info['path']]
        if verbose:
            cmd.append("-v")
        else:
            cmd.append("-q")
        
        cmd.extend(["--tb=short", "--no-header"])
        
        logger.info(f"Running command: {' '.join(cmd)}")
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=Path.cwd()
            )
            
            success = result.returncode == 0
            
            if success:
                logger.info(f"✅ {category} tests PASSED")
                if verbose and result.stdout:
                    logger.info("Test output:")
                    logger.info(result.stdout)
            else:
                logger.error(f"❌ {category} tests FAILED")
                if result.stdout:
                    logger.error("Test output:")
                    logger.error(result.stdout)
                if result.stderr:
                    logger.error("Error output:")
                    logger.error(result.stderr)
            
            self.results[category] = {
                'success': success,
                'stdout': result.stdout,
                'stderr': result.stderr
            }
            
            return success
            
        except Exception as e:
            logger.error(f"Error running {category} tests: {str(e)}")
            self.results[category] = {
                'success': False,
                'stdout': '',
                'stderr': str(e)
            }
            return False
    
    def run_all_categories(self, verbose: bool = False) -> bool:
        """Run all test categories."""
        logger.info("🚀 Running all test categories...")
        logger.info("=" * 60)
        
        all_passed = True
        passed_categories = []
        failed_categories = []
        
        for category in self.test_categories.keys():
            logger.info(f"\n📁 Testing category: {category}")
            logger.info("-" * 40)
            
            success = self.run_category(category, verbose)
            
            if success:
                passed_categories.append(category)
            else:
                failed_categories.append(category)
                all_passed = False
        
        # Summary
        logger.info("\n" + "=" * 60)
        logger.info("TEST SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Total categories: {len(self.test_categories)}")
        logger.info(f"Passed: {len(passed_categories)}")
        logger.info(f"Failed: {len(failed_categories)}")
        
        if passed_categories:
            logger.info("\n✅ PASSED CATEGORIES:")
            for category in passed_categories:
                logger.info(f"  - {category}")
        
        if failed_categories:
            logger.info("\n❌ FAILED CATEGORIES:")
            for category in failed_categories:
                logger.info(f"  - {category}")
        
        if all_passed:
            logger.info("\n🎉 ALL TESTS PASSED!")
        else:
            logger.info("\n🛑 SOME TESTS FAILED!")
        
        return all_passed
    
    def run_specific_files(self, files: List[str], verbose: bool = False) -> bool:
        """Run specific test files."""
        logger.info(f"Running specific test files: {files}")
        
        all_passed = True
        
        for file_path in files:
            logger.info(f"\n📄 Testing file: {file_path}")
            logger.info("-" * 40)
            
            # Check if file exists
            if not Path(file_path).exists():
                logger.error(f"File does not exist: {file_path}")
                all_passed = False
                continue
            
            # Run pytest on the specific file
            cmd = [sys.executable, "-m", "pytest", file_path]
            if verbose:
                cmd.append("-v")
            else:
                cmd.append("-q")
            
            cmd.extend(["--tb=short", "--no-header"])
            
            try:
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    cwd=Path.cwd()
                )
                
                success = result.returncode == 0
                
                if success:
                    logger.info(f"✅ {file_path} PASSED")
                else:
                    logger.error(f"❌ {file_path} FAILED")
                    if result.stdout:
                        logger.error("Test output:")
                        logger.error(result.stdout)
                    if result.stderr:
                        logger.error("Error output:")
                        logger.error(result.stderr)
                    all_passed = False
                
            except Exception as e:
                logger.error(f"Error running {file_path}: {str(e)}")
                all_passed = False
        
        return all_passed


def main():
    """Main function for the category test runner."""
    parser = argparse.ArgumentParser(description="CamProV5 Test Runner by Category")
    parser.add_argument("--category", "-c", help="Run tests for a specific category")
    parser.add_argument("--list", "-l", action="store_true", help="List all available categories")
    parser.add_argument("--all", "-a", action="store_true", help="Run all test categories")
    parser.add_argument("--files", "-f", nargs="+", help="Run specific test files")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    runner = CategoryTestRunner()
    
    if args.list:
        runner.list_categories()
        return True
    
    if args.category:
        success = runner.run_category(args.category, args.verbose)
        return success
    
    if args.files:
        success = runner.run_specific_files(args.files, args.verbose)
        return success
    
    if args.all:
        success = runner.run_all_categories(args.verbose)
        return success
    
    # Default: run all categories
    logger.info("No specific action specified. Running all test categories...")
    success = runner.run_all_categories(args.verbose)
    return success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
