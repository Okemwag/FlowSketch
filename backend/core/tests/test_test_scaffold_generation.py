"""
Unit tests for test scaffold generation functionality.
"""

import pytest

from core.services.diagram_engine import DiagramData, Edge, Node, Position
from core.services.specification_generator import (AcceptanceCriterion,
                                                   ProgrammingLanguage,
                                                   SpecificationGenerator,
                                                   TestCase, TestFile,
                                                   TestScaffold, TestType)
from core.services.text_parser import DiagramType


class TestTestScaffoldGeneration:
    """Test cases for test scaffold generation."""

    def setup_method(self):
        """Set up test fixtures."""
        self.generator = SpecificationGenerator()
        
        # Sample diagram data for testing
        self.sample_nodes = [
            Node(
                id="user_1",
                label="User",
                shape="circle",
                entity_type="actor",
                properties={"role": "customer"},
                position=Position(100, 100),
            ),
            Node(
                id="system_1",
                label="Login System",
                shape="hexagon",
                entity_type="system",
                properties={"type": "authentication"},
                position=Position(300, 100),
            ),
            Node(
                id="database_1",
                label="User Database",
                shape="cylinder",
                entity_type="data",
                properties={"type": "storage"},
                position=Position(500, 100),
            ),
        ]
        
        self.sample_edges = [
            Edge(
                source_id="user_1",
                target_id="system_1",
                label="authenticates with",
                arrow_type="-.->",
                relationship_type="uses",
            ),
            Edge(
                source_id="system_1",
                target_id="database_1",
                label="queries user data",
                arrow_type="..>",
                relationship_type="accesses",
            ),
        ]
        
        self.sample_diagram_data = DiagramData(
            diagram_type=DiagramType.FLOWCHART,
            mermaid_syntax="flowchart TD\n    user_1((User))\n    system_1{Login System}\n    database_1[(User Database)]",
            nodes=self.sample_nodes,
            edges=self.sample_edges,
            layout_config={"direction": "TD", "theme": "default"},
            metadata={"entity_count": "3", "relationship_count": "2"},
        )
        
        self.sample_acceptance_criteria = [
            AcceptanceCriterion(
                id="1",
                description="User must be able to authenticate successfully",
                priority="high",
                category="functional",
                related_entities=["User", "Login System"],
                test_scenarios=["Valid credentials", "Invalid credentials"]
            ),
            AcceptanceCriterion(
                id="2",
                description="System must validate user data from database",
                priority="medium",
                category="functional",
                related_entities=["Login System", "User Database"],
                test_scenarios=["Database query", "Data validation"]
            ),
        ]

    def test_generate_test_scaffold_basic(self):
        """Test basic test scaffold generation."""
        result = self.generator.generate_test_scaffold(
            self.sample_diagram_data, 
            self.sample_acceptance_criteria,
            ProgrammingLanguage.PYTHON
        )
        
        assert isinstance(result, TestScaffold)
        assert result.language == ProgrammingLanguage.PYTHON
        assert len(result.test_files) > 0
        assert result.setup_instructions
        assert result.run_instructions
        assert len(result.dependencies) > 0

    def test_generate_test_scaffold_different_languages(self):
        """Test test scaffold generation for different programming languages."""
        languages = [
            ProgrammingLanguage.PYTHON,
            ProgrammingLanguage.JAVASCRIPT,
            ProgrammingLanguage.JAVA,
        ]
        
        for language in languages:
            result = self.generator.generate_test_scaffold(
                self.sample_diagram_data, 
                self.sample_acceptance_criteria,
                language
            )
            
            assert result.language == language
            assert len(result.test_files) > 0
            assert result.setup_instructions
            assert result.run_instructions
            assert len(result.dependencies) > 0

    def test_unit_test_file_generation(self):
        """Test unit test file generation."""
        unit_test_file = self.generator._generate_unit_test_file(
            self.sample_diagram_data,
            self.sample_acceptance_criteria,
            ProgrammingLanguage.PYTHON
        )
        
        assert isinstance(unit_test_file, TestFile)
        assert unit_test_file.filename == "test_components.py"
        assert unit_test_file.language == ProgrammingLanguage.PYTHON
        assert len(unit_test_file.imports) > 0
        assert len(unit_test_file.test_cases) > 0
        assert unit_test_file.full_content
        
        # Check that test cases are generated for each node
        node_names = [node.label for node in self.sample_nodes]
        for node_name in node_names:
            assert any(node_name.lower().replace(' ', '_') in test_case.name for test_case in unit_test_file.test_cases)

    def test_integration_test_file_generation(self):
        """Test integration test file generation."""
        integration_test_file = self.generator._generate_integration_test_file(
            self.sample_diagram_data,
            self.sample_acceptance_criteria,
            ProgrammingLanguage.PYTHON
        )
        
        assert isinstance(integration_test_file, TestFile)
        assert integration_test_file.filename == "test_integrations.py"
        assert integration_test_file.language == ProgrammingLanguage.PYTHON
        assert len(integration_test_file.test_cases) > 0
        
        # Check that test cases are generated for relationships
        assert len(integration_test_file.test_cases) >= len(self.sample_edges) * 2  # Success + failure tests

    def test_e2e_test_file_generation(self):
        """Test E2E test file generation."""
        e2e_test_file = self.generator._generate_e2e_test_file(
            self.sample_diagram_data,
            self.sample_acceptance_criteria,
            ProgrammingLanguage.PYTHON
        )
        
        assert isinstance(e2e_test_file, TestFile)
        assert e2e_test_file.filename == "test_e2e.py"
        assert e2e_test_file.language == ProgrammingLanguage.PYTHON
        assert len(e2e_test_file.test_cases) > 0

    def test_node_unit_tests_generation(self):
        """Test unit test generation for nodes."""
        node = self.sample_nodes[0]  # User node
        test_cases = self.generator._generate_node_unit_tests(
            node, 
            self.sample_acceptance_criteria,
            ProgrammingLanguage.PYTHON
        )
        
        assert len(test_cases) > 0
        
        # Should have basic functionality, validation, and error handling tests
        test_types = [test_case.name for test_case in test_cases]
        assert any("basic_functionality" in name for name in test_types)
        assert any("validation" in name for name in test_types)
        assert any("error_handling" in name for name in test_types)

    def test_edge_integration_tests_generation(self):
        """Test integration test generation for edges."""
        edge = self.sample_edges[0]  # User -> Login System
        test_cases = self.generator._generate_edge_integration_tests(
            edge,
            self.sample_nodes,
            self.sample_acceptance_criteria,
            ProgrammingLanguage.PYTHON
        )
        
        assert len(test_cases) >= 2  # Success and failure tests
        
        # Check test case names include relationship type
        test_names = [test_case.name for test_case in test_cases]
        assert any("success" in name for name in test_names)
        assert any("failure" in name for name in test_names)

    def test_basic_functionality_test_generation(self):
        """Test basic functionality test generation."""
        node = self.sample_nodes[1]  # Login System
        test_case = self.generator._generate_basic_functionality_test(
            node, ProgrammingLanguage.PYTHON
        )
        
        assert isinstance(test_case, TestCase)
        assert test_case.test_type == TestType.UNIT
        assert "basic_functionality" in test_case.name
        assert "Login System" in test_case.description
        assert test_case.setup_code
        assert test_case.test_code
        assert len(test_case.assertions) > 0

    def test_validation_test_generation(self):
        """Test validation test generation."""
        node = self.sample_nodes[1]  # Login System
        test_case = self.generator._generate_validation_test(
            node, ProgrammingLanguage.PYTHON
        )
        
        assert isinstance(test_case, TestCase)
        assert test_case.test_type == TestType.UNIT
        assert "validation" in test_case.name
        assert "validation" in test_case.description.lower()
        assert "assertRaises" in test_case.test_code or "ValidationError" in test_case.test_code

    def test_error_handling_test_generation(self):
        """Test error handling test generation."""
        node = self.sample_nodes[1]  # Login System
        test_case = self.generator._generate_error_handling_test(
            node, ProgrammingLanguage.PYTHON
        )
        
        assert isinstance(test_case, TestCase)
        assert test_case.test_type == TestType.UNIT
        assert "error_handling" in test_case.name
        assert "error" in test_case.description.lower()

    def test_acceptance_criteria_test_generation(self):
        """Test acceptance criteria test generation."""
        node = self.sample_nodes[0]  # User
        criterion = self.sample_acceptance_criteria[0]
        test_case = self.generator._generate_acceptance_criteria_test(
            node, criterion, ProgrammingLanguage.PYTHON
        )
        
        assert isinstance(test_case, TestCase)
        assert test_case.test_type == TestType.UNIT
        assert f"ac_{criterion.id}" in test_case.name
        assert criterion.id in test_case.related_acceptance_criteria

    def test_successful_interaction_test_generation(self):
        """Test successful interaction test generation."""
        source = self.sample_nodes[0]  # User
        target = self.sample_nodes[1]  # Login System
        edge = self.sample_edges[0]    # uses relationship
        
        test_case = self.generator._generate_successful_interaction_test(
            source, target, edge, ProgrammingLanguage.PYTHON
        )
        
        assert isinstance(test_case, TestCase)
        assert test_case.test_type == TestType.INTEGRATION
        assert "success" in test_case.name
        assert edge.relationship_type in test_case.name
        assert source.label.lower().replace(' ', '_') in test_case.name
        assert target.label.lower().replace(' ', '_') in test_case.name

    def test_interaction_failure_test_generation(self):
        """Test interaction failure test generation."""
        source = self.sample_nodes[0]  # User
        target = self.sample_nodes[1]  # Login System
        edge = self.sample_edges[0]    # uses relationship
        
        test_case = self.generator._generate_interaction_failure_test(
            source, target, edge, ProgrammingLanguage.PYTHON
        )
        
        assert isinstance(test_case, TestCase)
        assert test_case.test_type == TestType.INTEGRATION
        assert "failure" in test_case.name
        assert "assertFalse" in test_case.test_code

    def test_happy_path_test_generation(self):
        """Test happy path E2E test generation."""
        workflow = self.sample_nodes  # Use all nodes as workflow
        test_case = self.generator._generate_happy_path_test(
            workflow, ProgrammingLanguage.PYTHON
        )
        
        assert isinstance(test_case, TestCase)
        assert test_case.test_type == TestType.END_TO_END
        assert "happy_path" in test_case.name
        assert workflow[0].label in test_case.description
        assert workflow[-1].label in test_case.description

    def test_error_path_test_generation(self):
        """Test error path E2E test generation."""
        workflow = self.sample_nodes  # Use all nodes as workflow
        test_case = self.generator._generate_error_path_test(
            workflow, ProgrammingLanguage.PYTHON
        )
        
        assert isinstance(test_case, TestCase)
        assert test_case.test_type == TestType.END_TO_END
        assert "error_path" in test_case.name
        assert "error" in test_case.description.lower()

    def test_language_specific_imports(self):
        """Test language-specific import generation."""
        # Test Python imports
        python_imports = self.generator._get_unit_test_imports(ProgrammingLanguage.PYTHON)
        assert "unittest" in " ".join(python_imports)
        assert "pytest" in " ".join(python_imports)
        
        # Test JavaScript imports
        js_imports = self.generator._get_unit_test_imports(ProgrammingLanguage.JAVASCRIPT)
        assert "jest" in " ".join(js_imports)
        assert "expect" in " ".join(js_imports)
        
        # Test Java imports
        java_imports = self.generator._get_unit_test_imports(ProgrammingLanguage.JAVA)
        assert "junit" in " ".join(java_imports)
        assert "Test" in " ".join(java_imports)

    def test_language_specific_setup_code(self):
        """Test language-specific setup code generation."""
        # Test Python setup
        python_setup = self.generator._get_unit_test_setup(ProgrammingLanguage.PYTHON)
        assert "unittest.TestCase" in python_setup
        assert "setUp" in python_setup
        
        # Test JavaScript setup
        js_setup = self.generator._get_unit_test_setup(ProgrammingLanguage.JAVASCRIPT)
        assert "describe" in js_setup
        assert "beforeEach" in js_setup
        
        # Test Java setup
        java_setup = self.generator._get_unit_test_setup(ProgrammingLanguage.JAVA)
        assert "BeforeEach" in java_setup
        assert "setUp" in java_setup

    def test_language_specific_filenames(self):
        """Test language-specific filename generation."""
        # Test Python filenames
        assert self.generator._get_unit_test_filename(ProgrammingLanguage.PYTHON) == "test_components.py"
        assert self.generator._get_integration_test_filename(ProgrammingLanguage.PYTHON) == "test_integrations.py"
        assert self.generator._get_e2e_test_filename(ProgrammingLanguage.PYTHON) == "test_e2e.py"
        
        # Test JavaScript filenames
        assert self.generator._get_unit_test_filename(ProgrammingLanguage.JAVASCRIPT) == "components.test.js"
        assert self.generator._get_integration_test_filename(ProgrammingLanguage.JAVASCRIPT) == "integrations.test.js"
        assert self.generator._get_e2e_test_filename(ProgrammingLanguage.JAVASCRIPT) == "e2e.test.js"
        
        # Test Java filenames
        assert self.generator._get_unit_test_filename(ProgrammingLanguage.JAVA) == "ComponentTests.java"
        assert self.generator._get_integration_test_filename(ProgrammingLanguage.JAVA) == "IntegrationTests.java"
        assert self.generator._get_e2e_test_filename(ProgrammingLanguage.JAVA) == "EndToEndTests.java"

    def test_test_dependencies_generation(self):
        """Test test dependencies generation."""
        # Test Python dependencies
        python_deps = self.generator._get_test_dependencies(ProgrammingLanguage.PYTHON)
        assert any("pytest" in dep for dep in python_deps)
        assert any("selenium" in dep for dep in python_deps)
        
        # Test JavaScript dependencies
        js_deps = self.generator._get_test_dependencies(ProgrammingLanguage.JAVASCRIPT)
        assert any("jest" in dep for dep in js_deps)
        assert any("puppeteer" in dep for dep in js_deps)
        
        # Test Java dependencies
        java_deps = self.generator._get_test_dependencies(ProgrammingLanguage.JAVA)
        assert any("junit" in dep for dep in java_deps)
        assert any("selenium" in dep for dep in java_deps)

    def test_setup_instructions_generation(self):
        """Test setup instructions generation."""
        for language in [ProgrammingLanguage.PYTHON, ProgrammingLanguage.JAVASCRIPT, ProgrammingLanguage.JAVA]:
            instructions = self.generator._generate_setup_instructions(language)
            assert "Prerequisites" in instructions
            assert "Installation" in instructions
            assert "Configuration" in instructions
            assert len(instructions) > 100  # Should be substantial

    def test_run_instructions_generation(self):
        """Test run instructions generation."""
        for language in [ProgrammingLanguage.PYTHON, ProgrammingLanguage.JAVASCRIPT, ProgrammingLanguage.JAVA]:
            instructions = self.generator._generate_run_instructions(language)
            assert "Running Tests" in instructions
            assert "All Tests" in instructions
            assert len(instructions) > 100  # Should be substantial

    def test_test_file_content_generation(self):
        """Test complete test file content generation."""
        imports = ["import unittest", "import pytest"]
        setup_code = "class TestExample(unittest.TestCase):"
        test_cases = [
            TestCase(
                name="test_example",
                description="Example test",
                test_type=TestType.UNIT,
                setup_code="# Setup",
                test_code="# Test",
                teardown_code="# Teardown",
                assertions=["Assert something"],
                related_acceptance_criteria=[]
            )
        ]
        helper_methods = ["def helper_method(self): pass"]
        
        content = self.generator._generate_test_file_content(
            "unit_tests", imports, setup_code, test_cases, helper_methods, ProgrammingLanguage.PYTHON
        )
        
        assert "Generated unit_tests tests" in content
        assert "import unittest" in content
        assert "import pytest" in content
        assert "class TestExample" in content
        assert "test_example" in content
        assert "helper_method" in content

    def test_test_case_formatting(self):
        """Test test case formatting for different languages."""
        test_case = TestCase(
            name="test_example",
            description="Example test case",
            test_type=TestType.UNIT,
            setup_code="# Setup code",
            test_code="# Test code",
            teardown_code="# Teardown code",
            assertions=["Assert something"],
            related_acceptance_criteria=[]
        )
        
        # Test Python formatting
        python_formatted = self.generator._format_test_case(test_case, ProgrammingLanguage.PYTHON)
        assert "def test_example(self):" in python_formatted
        assert '"""' in python_formatted
        
        # Test JavaScript formatting
        js_formatted = self.generator._format_test_case(test_case, ProgrammingLanguage.JAVASCRIPT)
        assert "it('Example test case'" in js_formatted
        assert "});" in js_formatted
        
        # Test Java formatting
        java_formatted = self.generator._format_test_case(test_case, ProgrammingLanguage.JAVA)
        assert "@Test" in java_formatted
        assert "void test_example()" in java_formatted

    def test_workflow_identification(self):
        """Test workflow identification for E2E tests."""
        workflows = self.generator._identify_workflows(self.sample_diagram_data)
        
        assert isinstance(workflows, list)
        # Should identify at least one workflow from the connected nodes
        if workflows:
            assert all(isinstance(workflow, list) for workflow in workflows)
            assert all(len(workflow) > 1 for workflow in workflows)

    def test_specification_with_test_scaffold(self):
        """Test specification generation with test scaffold included."""
        result = self.generator.generate_specification(
            self.sample_diagram_data, 
            "Test System",
            include_tests=True,
            test_language=ProgrammingLanguage.PYTHON
        )
        
        assert result.test_scaffold is not None
        assert isinstance(result.test_scaffold, TestScaffold)
        assert result.test_scaffold.language == ProgrammingLanguage.PYTHON
        assert len(result.test_scaffold.test_files) > 0
        
        # Check metadata includes test information
        assert result.metadata["includes_tests"] is True
        assert result.metadata["test_language"] == "python"

    def test_specification_without_test_scaffold(self):
        """Test specification generation without test scaffold."""
        result = self.generator.generate_specification(
            self.sample_diagram_data, 
            "Test System",
            include_tests=False
        )
        
        assert result.test_scaffold is None
        assert result.metadata["includes_tests"] is False
        assert result.metadata["test_language"] is None

    def test_complex_diagram_test_generation(self):
        """Test test generation for a more complex diagram."""
        # Create a more complex diagram
        complex_nodes = [
            Node(f"node_{i}", f"Component {i}", "rect", "system", {}, Position(i*100, 100))
            for i in range(5)
        ]
        
        complex_edges = [
            Edge(f"node_{i}", f"node_{i+1}", f"flow {i}", "-->", "uses")
            for i in range(4)
        ]
        
        complex_diagram = DiagramData(
            diagram_type=DiagramType.FLOWCHART,
            mermaid_syntax="complex flowchart",
            nodes=complex_nodes,
            edges=complex_edges,
            layout_config={},
            metadata={},
        )
        
        test_scaffold = self.generator.generate_test_scaffold(
            complex_diagram, 
            self.sample_acceptance_criteria,
            ProgrammingLanguage.PYTHON
        )
        
        assert len(test_scaffold.test_files) >= 2  # At least unit and integration tests
        
        # Should have more test cases due to more components
        total_test_cases = sum(len(file.test_cases) for file in test_scaffold.test_files)
        assert total_test_cases > 10  # Should have many test cases

    def test_test_scaffold_metadata(self):
        """Test test scaffold metadata generation."""
        test_scaffold = self.generator.generate_test_scaffold(
            self.sample_diagram_data, 
            self.sample_acceptance_criteria,
            ProgrammingLanguage.PYTHON
        )
        
        metadata = test_scaffold.metadata
        
        expected_keys = [
            "generated_at", "language", "test_file_count", 
            "total_test_cases", "diagram_type"
        ]
        
        for key in expected_keys:
            assert key in metadata
        
        assert metadata["language"] == "python"
        assert metadata["test_file_count"] == len(test_scaffold.test_files)
        assert metadata["diagram_type"] == "flowchart"