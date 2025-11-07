#!/bin/bash
# lightspeed:PIPELINE System Validation Script

echo "🔍 lightspeed:PIPELINE System Validation"
echo "=================================="

VALIDATION_REPORT="artifacts/system-validation-report.md"
mkdir -p artifacts
echo "# lightspeed:PIPELINE System Validation Report" > "$VALIDATION_REPORT"
echo "Generated: $(date)" >> "$VALIDATION_REPORT"
echo "" >> "$VALIDATION_REPORT"

ERRORS=0
WARNINGS=0

log_success() {
    echo "✅ $1"
    echo "- [x] $1" >> "$VALIDATION_REPORT"
}

log_error() {
    echo "❌ $1"
    echo "- [ ] ❌ $1" >> "$VALIDATION_REPORT"
    ((ERRORS++))
}

log_warning() {
    echo "⚠️ $1"
    echo "- [ ] ⚠️ $1" >> "$VALIDATION_REPORT"
    ((WARNINGS++))
}

echo "" >> "$VALIDATION_REPORT"
echo "## Directory Structure Validation" >> "$VALIDATION_REPORT"

# Validate directory structure
echo "🏗️ Validating Directory Structure..."

if [ -d ".claude" ]; then
    log_success "Claude configuration directory exists"
else
    log_error "Claude configuration directory missing"
fi

if [ -d ".claude/commands" ]; then
    log_success "Commands directory exists"
else
    log_error "Commands directory missing"
fi

if [ -d ".claude/agents" ]; then
    log_success "Agents directory exists"
else
    log_error "Agents directory missing"
fi

if [ -d "project/frontend" ]; then
    log_success "Frontend project directory exists"
else
    log_error "Frontend project directory missing"
fi

if [ -d "project/backend" ]; then
    log_success "Backend project directory exists"
else
    log_error "Backend project directory missing"
fi

if [ -d "project/infrastructure" ]; then
    log_success "Infrastructure directory exists"
else
    log_error "Infrastructure directory missing"
fi

if [ -d "artifacts" ]; then
    log_success "Artifacts directory exists"
else
    log_error "Artifacts directory missing"
fi

echo "" >> "$VALIDATION_REPORT"
echo "## Core Commands Validation" >> "$VALIDATION_REPORT"

# Validate core command files
echo "📋 Validating Core Commands..."

if [ -f ".claude/commands/lightspeed-pipeline.md" ]; then
    log_success "lightspeed-pipeline command exists"
    
    if grep -q "lightspeed:PIPELINE" ".claude/commands/lightspeed-pipeline.md"; then
        log_success "lightspeed-pipeline command has proper header"
    else
        log_error "lightspeed-pipeline command missing proper header"
    fi
    
    if grep -q "PHASE 1: EXPLORATION" ".claude/commands/lightspeed-pipeline.md"; then
        log_success "lightspeed-pipeline includes exploration phase"
    else
        log_error "lightspeed-pipeline missing exploration phase"
    fi
    
    if grep -q "PHASE 2: PLANNING" ".claude/commands/lightspeed-pipeline.md"; then
        log_success "lightspeed-pipeline includes planning phase"
    else
        log_error "lightspeed-pipeline missing planning phase"
    fi
    
    if grep -q "PHASE 3: CODE IMPLEMENTATION" ".claude/commands/lightspeed-pipeline.md"; then
        log_success "lightspeed-pipeline includes code implementation phase"
    else
        log_error "lightspeed-pipeline missing code implementation phase"
    fi
    
else
    log_error "lightspeed-pipeline command file missing"
fi

echo "" >> "$VALIDATION_REPORT"
echo "## Specialized Agents Validation" >> "$VALIDATION_REPORT"

# Validate agent files
echo "🤖 Validating Specialized Agents..."

REQUIRED_AGENTS=(
    "design-system-agent.md"
    "terraform-agent.md"
    "react-expert.md"
    "backend-engineer.md"
    "api-designer.md"
)

for agent in "${REQUIRED_AGENTS[@]}"; do
    if [ -f ".claude/agents/$agent" ]; then
        log_success "Agent $agent exists"
        
        if grep -q "role:" ".claude/agents/$agent"; then
            log_success "$agent has proper role definition"
        else
            log_error "$agent missing role definition"
        fi
        
        if grep -q "WHEN ACTIVATED" ".claude/agents/$agent"; then
            log_success "$agent has activation instructions"
        else
            log_error "$agent missing activation instructions"
        fi
        
    else
        log_error "Agent $agent missing"
    fi
done

echo "" >> "$VALIDATION_REPORT"
echo "## Template Files Validation" >> "$VALIDATION_REPORT"

# Validate template files
echo "📄 Validating Template Files..."

if [ -f ".claude/templates/epcc-commands.md" ]; then
    log_success "EPCC commands template exists"
    
    if grep -q "EPCC-EXPLORE Command" ".claude/templates/epcc-commands.md"; then
        log_success "EPCC-EXPLORE template included"
    else
        log_error "EPCC-EXPLORE template missing"
    fi
    
    if grep -q "EPCC-PLAN Command" ".claude/templates/epcc-commands.md"; then
        log_success "EPCC-PLAN template included"
    else
        log_error "EPCC-PLAN template missing"
    fi
    
    if grep -q "EPCC-CODE Command" ".claude/templates/epcc-commands.md"; then
        log_success "EPCC-CODE template included"
    else
        log_error "EPCC-CODE template missing"
    fi
    
    if grep -q "EPCC-COMMIT Command" ".claude/templates/epcc-commands.md"; then
        log_success "EPCC-COMMIT template included"
    else
        log_error "EPCC-COMMIT template missing"
    fi
    
else
    log_error "EPCC commands template missing"
fi

echo "" >> "$VALIDATION_REPORT"
echo "## lightspeed Design System Validation" >> "$VALIDATION_REPORT"

# Validate lightspeed Design System integration
echo "🎨 Validating lightspeed Design System Integration..."

if [ -f "project/design_system/lightspeed-design-system.md" ]; then
    log_success "lightspeed Design System specification exists"
    
    if grep -q "#954293" "project/design_system/lightspeed-design-system.md"; then
        log_success "lightspeed purple color (#954293) specified"
    else
        log_error "lightspeed purple color (#954293) not found"
    fi
    
    if grep -q "#00857f" "project/design_system/lightspeed-design-system.md"; then
        log_success "lightspeed teal color (#00857f) specified"
    else
        log_error "lightspeed teal color (#00857f) not found"
    fi
    
    if grep -q "Poppins" "project/design_system/lightspeed-design-system.md"; then
        log_success "Poppins font family specified"
    else
        log_error "Poppins font family not found"
    fi
    
else
    log_error "lightspeed Design System specification missing"
fi

echo "" >> "$VALIDATION_REPORT"
echo "## Agent Capabilities Validation" >> "$VALIDATION_REPORT"

# Validate agent capabilities
echo "⚙️ Validating Agent Capabilities..."

if [ -f ".claude/agents/design-system-agent.md" ]; then
    if grep -q "BUILD COMPLETE DESIGN SYSTEMS" ".claude/agents/design-system-agent.md"; then
        log_success "Design System Agent has complete implementation capability"
    else
        log_error "Design System Agent missing complete implementation capability"
    fi
    
    if grep -q "lightspeed COMPLIANCE" ".claude/agents/design-system-agent.md"; then
        log_success "Design System Agent includes lightspeed compliance"
    else
        log_warning "Design System Agent should include lightspeed compliance"
    fi
fi

if [ -f ".claude/agents/terraform-agent.md" ]; then
    if grep -q "ZERO-COST" ".claude/agents/terraform-agent.md"; then
        log_success "Terraform Agent includes zero-cost architecture"
    else
        log_error "Terraform Agent missing zero-cost architecture"
    fi
    
    if grep -q "COMPLETE TERRAFORM CONFIGURATIONS" ".claude/agents/terraform-agent.md"; then
        log_success "Terraform Agent has complete configuration capability"
    else
        log_error "Terraform Agent missing complete configuration capability"
    fi
fi

if [ -f ".claude/agents/react-expert.md" ]; then
    if grep -q "COMPLETE REACT APPLICATIONS" ".claude/agents/react-expert.md"; then
        log_success "React Expert has complete application capability"
    else
        log_error "React Expert missing complete application capability"
    fi
    
    if grep -q "TypeScript" ".claude/agents/react-expert.md"; then
        log_success "React Expert includes TypeScript support"
    else
        log_error "React Expert missing TypeScript support"
    fi
fi

echo "" >> "$VALIDATION_REPORT"
echo "## Documentation Routing Validation" >> "$VALIDATION_REPORT"

# Validate documentation routing
echo "📚 Validating Documentation Routing..."

if grep -q "artifacts/Explore/" ".claude/commands/lightspeed-pipeline.md"; then
    log_success "Exploration phase routes to artifacts/Explore/"
else
    log_error "Exploration phase missing proper routing"
fi

if grep -q "artifacts/Plan/" ".claude/commands/lightspeed-pipeline.md"; then
    log_success "Planning phase routes to artifacts/Plan/"
else
    log_error "Planning phase missing proper routing"
fi

if grep -q "artifacts/Code/" ".claude/commands/lightspeed-pipeline.md"; then
    log_success "Code phase routes to artifacts/Code/"
else
    log_error "Code phase missing proper routing"
fi

if grep -q "artifacts/Commit/" ".claude/commands/lightspeed-pipeline.md"; then
    log_success "Commit phase routes to artifacts/Commit/"
else
    log_error "Commit phase missing proper routing"
fi

echo "" >> "$VALIDATION_REPORT"
echo "## Security Validation" >> "$VALIDATION_REPORT"

# Basic security checks
echo "🔒 Validating Security Configuration..."

if grep -iq "password" .claude/agents/*.md .claude/commands/*.md .claude/templates/*.md 2>/dev/null; then
    log_warning "Password references found in configuration files"
else
    log_success "No password references in configuration files"
fi

if grep -iq "secret" .claude/agents/*.md .claude/commands/*.md .claude/templates/*.md 2>/dev/null; then
    log_warning "Secret references found in configuration files"
else
    log_success "No secret references in configuration files"
fi

if grep -iq "key" .claude/agents/*.md .claude/commands/*.md .claude/templates/*.md 2>/dev/null; then
    log_warning "Key references found in configuration files (review for secrets)"
else
    log_success "No key references in configuration files"
fi

# Final validation summary
echo "" >> "$VALIDATION_REPORT"
echo "## Validation Summary" >> "$VALIDATION_REPORT"
echo "- **Errors**: $ERRORS" >> "$VALIDATION_REPORT"
echo "- **Warnings**: $WARNINGS" >> "$VALIDATION_REPORT"
echo "- **Status**: $(if [ $ERRORS -eq 0 ]; then echo "✅ PASSED"; else echo "❌ FAILED"; fi)" >> "$VALIDATION_REPORT"

echo ""
echo "📊 Validation Summary:"
echo "   Errors: $ERRORS"
echo "   Warnings: $WARNINGS"
echo "   Status: $(if [ $ERRORS -eq 0 ]; then echo "✅ PASSED"; else echo "❌ FAILED"; fi)"
echo ""
echo "📋 Full report saved to: $VALIDATION_REPORT"

if [ $ERRORS -eq 0 ]; then
    echo ""
    echo "🎉 lightspeed:PIPELINE System Validation PASSED!"
    echo "   The system is ready for production use."
    echo ""
    echo "🚀 To run the complete pipeline:"
    echo "   /lightspeed-pipeline \"my-project\" --full --timer"
    echo ""
    exit 0
else
    echo ""
    echo "❌ lightspeed:PIPELINE System Validation FAILED!"
    echo "   Please fix the errors above before using the system."
    echo ""
    exit 1
fi