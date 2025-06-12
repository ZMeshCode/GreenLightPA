#!/bin/bash
# 🔑 GreenLightPA API Keys Setup Script
# Interactive configuration for hybrid N8n + LangChain + Supabase architecture

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration files
ENV_FILE=".env"
ENV_DEV_FILE=".env.development"
ENV_EXAMPLE="config.example.env"

echo -e "${BLUE}🔑 GreenLightPA API Keys & Configuration Setup${NC}"
echo -e "${BLUE}================================================${NC}"
echo ""

# Check if running in development or production mode
read -p "$(echo -e ${YELLOW}📋 Setup for [d]evelopment or [p]roduction? ${NC})" -n 1 -r
echo ""
if [[ $REPLY =~ ^[Pp]$ ]]; then
    ENVIRONMENT="production"
    TARGET_FILE="$ENV_FILE"
    echo -e "${GREEN}🚀 Setting up PRODUCTION environment${NC}"
else
    ENVIRONMENT="development"
    TARGET_FILE="$ENV_DEV_FILE"
    echo -e "${CYAN}🛠️  Setting up DEVELOPMENT environment${NC}"
fi

echo ""

# Create backup of existing file if it exists
if [[ -f "$TARGET_FILE" ]]; then
    cp "$TARGET_FILE" "${TARGET_FILE}.backup.$(date +%Y%m%d_%H%M%S)"
    echo -e "${YELLOW}📁 Backed up existing $TARGET_FILE${NC}"
fi

# Start with the example file as base
if [[ -f "$ENV_EXAMPLE" ]]; then
    cp "$ENV_EXAMPLE" "$TARGET_FILE"
    echo -e "${GREEN}📋 Created $TARGET_FILE from template${NC}"
else
    touch "$TARGET_FILE"
    echo -e "${YELLOW}📋 Created new $TARGET_FILE${NC}"
fi

echo ""

# Function to prompt for configuration
prompt_config() {
    local var_name="$1"
    local description="$2"
    local default_value="$3"
    local is_secret="$4"
    
    echo -e "${CYAN}🔧 $description${NC}"
    
    if [[ "$is_secret" == "true" ]]; then
        echo -e "${YELLOW}⚠️  This is a secret value - input will be hidden${NC}"
        read -s -p "Enter $var_name: " value
        echo ""
    else
        if [[ -n "$default_value" ]]; then
            read -p "Enter $var_name [$default_value]: " value
            value="${value:-$default_value}"
        else
            read -p "Enter $var_name: " value
        fi
    fi
    
    # Update the configuration file
    if grep -q "^$var_name=" "$TARGET_FILE"; then
        # Update existing line
        if [[ "$OSTYPE" == "darwin"* ]]; then
            sed -i '' "s|^$var_name=.*|$var_name=$value|" "$TARGET_FILE"
        else
            sed -i "s|^$var_name=.*|$var_name=$value|" "$TARGET_FILE"
        fi
    else
        # Add new line
        echo "$var_name=$value" >> "$TARGET_FILE"
    fi
    
    echo -e "${GREEN}✅ $var_name configured${NC}"
    echo ""
}

# Function to generate secure random string
generate_secret() {
    openssl rand -base64 32 | tr -d "=+/" | cut -c1-32
}

# Function to generate Fernet key
generate_fernet_key() {
    python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())" 2>/dev/null || echo "$(generate_secret)"
}

echo -e "${PURPLE}🏗️  INFRASTRUCTURE CONFIGURATION${NC}"
echo -e "${PURPLE}=================================${NC}"

# Environment configuration
echo "ENVIRONMENT=$ENVIRONMENT" > "$TARGET_FILE"
if [[ "$ENVIRONMENT" == "development" ]]; then
    echo "DEBUG=true" >> "$TARGET_FILE"
    echo "LOG_LEVEL=DEBUG" >> "$TARGET_FILE"
else
    echo "DEBUG=false" >> "$TARGET_FILE"
    echo "LOG_LEVEL=INFO" >> "$TARGET_FILE"
fi

echo ""
echo -e "${BLUE}🐘 SUPABASE CONFIGURATION${NC}"
echo -e "${BLUE}=========================${NC}"

echo -e "${CYAN}Please create a Supabase project at https://supabase.com${NC}"
echo -e "${CYAN}Get your credentials from Settings > API${NC}"
echo ""

prompt_config "SUPABASE_URL" "Supabase Project URL (e.g., https://xxx.supabase.co)" "" false
prompt_config "SUPABASE_ANON_KEY" "Supabase Anonymous Key" "" true
prompt_config "SUPABASE_SERVICE_ROLE_KEY" "Supabase Service Role Key" "" true
prompt_config "SUPABASE_DB_PASSWORD" "Supabase Database Password" "" true

# Construct database URL
SUPABASE_URL_VALUE=$(grep "^SUPABASE_URL=" "$TARGET_FILE" | cut -d= -f2-)
SUPABASE_DB_PASSWORD_VALUE=$(grep "^SUPABASE_DB_PASSWORD=" "$TARGET_FILE" | cut -d= -f2-)
SUPABASE_HOST=$(echo "$SUPABASE_URL_VALUE" | sed 's|https://||' | sed 's|supabase\.co|db.&|')

echo "SUPABASE_DB_HOST=$SUPABASE_HOST" >> "$TARGET_FILE"
echo "SUPABASE_DATABASE_URL=postgresql://postgres:$SUPABASE_DB_PASSWORD_VALUE@$SUPABASE_HOST:5432/postgres" >> "$TARGET_FILE"

# For development, also set DATABASE_URL
if [[ "$ENVIRONMENT" == "development" ]]; then
    echo "DATABASE_URL=postgresql://postgres:$SUPABASE_DB_PASSWORD_VALUE@$SUPABASE_HOST:5432/postgres" >> "$TARGET_FILE"
fi

echo ""
echo -e "${BLUE}⚡ UPSTASH REDIS CONFIGURATION${NC}"
echo -e "${BLUE}=============================${NC}"

echo -e "${CYAN}Please create an Upstash Redis database at https://upstash.com${NC}"
echo -e "${CYAN}Get your credentials from Database > Details${NC}"
echo ""

prompt_config "UPSTASH_REDIS_REST_URL" "Upstash Redis REST URL" "" false
prompt_config "UPSTASH_REDIS_REST_TOKEN" "Upstash Redis REST Token" "" true
prompt_config "UPSTASH_REDIS_URL" "Upstash Redis URL (redis://...)" "" true

# Set Redis URL for the application
UPSTASH_REDIS_URL_VALUE=$(grep "^UPSTASH_REDIS_URL=" "$TARGET_FILE" | cut -d= -f2-)
echo "REDIS_URL=$UPSTASH_REDIS_URL_VALUE" >> "$TARGET_FILE"

echo ""
echo -e "${BLUE}🧠 AI SERVICES CONFIGURATION${NC}"
echo -e "${BLUE}===========================${NC}"

echo -e "${CYAN}Choose your LLM provider:${NC}"
echo -e "${CYAN}1) OpenAI (GPT-4, GPT-3.5)${NC}"
echo -e "${CYAN}2) Anthropic (Claude)${NC}"
echo -e "${CYAN}3) Both (OpenAI + Anthropic)${NC}"
echo ""

read -p "Select LLM provider [1/2/3]: " -n 1 -r
echo ""

case $REPLY in
    1)
        echo -e "${GREEN}🤖 Configuring OpenAI${NC}"
        echo -e "${CYAN}Get your OpenAI API key from https://platform.openai.com/api-keys${NC}"
        echo ""
        prompt_config "OPENAI_API_KEY" "OpenAI API Key" "" true
        echo "LLM_PROVIDER=openai" >> "$TARGET_FILE"
        echo "OPENAI_MODEL=gpt-4o" >> "$TARGET_FILE"
        ;;
    2)
        echo -e "${GREEN}🤖 Configuring Anthropic Claude${NC}"
        echo -e "${CYAN}Get your Anthropic API key from https://console.anthropic.com${NC}"
        echo ""
        prompt_config "ANTHROPIC_API_KEY" "Anthropic API Key" "" true
        echo "LLM_PROVIDER=anthropic" >> "$TARGET_FILE"
        echo "ANTHROPIC_MODEL=claude-3-5-sonnet-20241022" >> "$TARGET_FILE"
        ;;
    3)
        echo -e "${GREEN}🤖 Configuring Both OpenAI + Anthropic${NC}"
        echo ""
        echo -e "${CYAN}OpenAI Configuration:${NC}"
        echo -e "${CYAN}Get your OpenAI API key from https://platform.openai.com/api-keys${NC}"
        echo ""
        prompt_config "OPENAI_API_KEY" "OpenAI API Key" "" true
        echo ""
        echo -e "${CYAN}Anthropic Configuration:${NC}"
        echo -e "${CYAN}Get your Anthropic API key from https://console.anthropic.com${NC}"
        echo ""
        prompt_config "ANTHROPIC_API_KEY" "Anthropic API Key" "" true
        echo "LLM_PROVIDER=both" >> "$TARGET_FILE"
        echo "OPENAI_MODEL=gpt-4o" >> "$TARGET_FILE"
        echo "ANTHROPIC_MODEL=claude-3-5-sonnet-20241022" >> "$TARGET_FILE"
        ;;
    *)
        echo -e "${YELLOW}⚠️  Invalid selection, defaulting to Anthropic Claude${NC}"
        echo -e "${CYAN}Get your Anthropic API key from https://console.anthropic.com${NC}"
        echo ""
        prompt_config "ANTHROPIC_API_KEY" "Anthropic API Key" "" true
        echo "LLM_PROVIDER=anthropic" >> "$TARGET_FILE"
        echo "ANTHROPIC_MODEL=claude-3-5-sonnet-20241022" >> "$TARGET_FILE"
        ;;
esac

echo ""
echo -e "${CYAN}Optional: Get LangSmith API key from https://smith.langchain.com${NC}"
echo -e "${CYAN}(Press Enter to skip if you don't have one yet)${NC}"
echo ""

read -p "Do you want to configure LangSmith? [y/N]: " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    prompt_config "LANGCHAIN_API_KEY" "LangSmith API Key" "" true
    echo "LANGCHAIN_TRACING_V2=true" >> "$TARGET_FILE"
    echo "LANGCHAIN_ENDPOINT=https://api.smith.langchain.com" >> "$TARGET_FILE"
    
    if [[ "$ENVIRONMENT" == "development" ]]; then
        echo "LANGCHAIN_PROJECT=greenlightpa-dev" >> "$TARGET_FILE"
    else
        echo "LANGCHAIN_PROJECT=greenlightpa-prod" >> "$TARGET_FILE"
    fi
else
    echo "LANGCHAIN_TRACING_V2=false" >> "$TARGET_FILE"
fi

echo ""
echo -e "${BLUE}⚙️  N8N CONFIGURATION${NC}"
echo -e "${BLUE}===================${NC}"

# Generate N8n secrets
N8N_ENCRYPTION_KEY=$(generate_secret)
N8N_PASSWORD=$(generate_secret | cut -c1-16)

echo "N8N_ENCRYPTION_KEY=$N8N_ENCRYPTION_KEY" >> "$TARGET_FILE"
echo "N8N_BASIC_AUTH_ACTIVE=true" >> "$TARGET_FILE"
echo "N8N_BASIC_AUTH_USER=admin" >> "$TARGET_FILE"
echo "N8N_BASIC_AUTH_PASSWORD=$N8N_PASSWORD" >> "$TARGET_FILE"

if [[ "$ENVIRONMENT" == "development" ]]; then
    echo "N8N_HOST=localhost" >> "$TARGET_FILE"
    echo "N8N_PORT=5678" >> "$TARGET_FILE"
    echo "N8N_PROTOCOL=http" >> "$TARGET_FILE"
    echo "N8N_WEBHOOK_URL=http://localhost:5678/webhook" >> "$TARGET_FILE"
else
    echo "N8N_HOST=greenlightpa-n8n.fly.dev" >> "$TARGET_FILE"
    echo "N8N_PORT=5678" >> "$TARGET_FILE"
    echo "N8N_PROTOCOL=https" >> "$TARGET_FILE"
    echo "N8N_WEBHOOK_URL=https://greenlightpa-n8n.fly.dev/webhook" >> "$TARGET_FILE"
fi

echo -e "${GREEN}✅ N8n credentials generated automatically${NC}"
echo -e "${YELLOW}📝 N8n admin credentials:${NC}"
echo -e "${YELLOW}   Username: admin${NC}"
echo -e "${YELLOW}   Password: $N8N_PASSWORD${NC}"
echo -e "${YELLOW}💾 Save these credentials securely!${NC}"

echo ""
echo -e "${BLUE}🔐 SECURITY CONFIGURATION${NC}"
echo -e "${BLUE}=========================${NC}"

# Generate security secrets
SECRET_KEY=$(generate_secret)
JWT_SECRET_KEY=$(generate_secret)
FIELD_ENCRYPTION_KEY=$(generate_fernet_key)

echo "SECRET_KEY=$SECRET_KEY" >> "$TARGET_FILE"
echo "JWT_SECRET_KEY=$JWT_SECRET_KEY" >> "$TARGET_FILE"
echo "JWT_ALGORITHM=HS256" >> "$TARGET_FILE"
echo "JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30" >> "$TARGET_FILE"
echo "FIELD_ENCRYPTION_KEY=$FIELD_ENCRYPTION_KEY" >> "$TARGET_FILE"

if [[ "$ENVIRONMENT" == "development" ]]; then
    echo 'CORS_ORIGINS=["http://localhost:3000","http://localhost:8000","http://localhost:5678"]' >> "$TARGET_FILE"
else
    echo 'CORS_ORIGINS=["https://app.greenlightpa.com","https://greenlightpa-n8n.fly.dev"]' >> "$TARGET_FILE"
fi

echo -e "${GREEN}✅ Security secrets generated automatically${NC}"

echo ""
echo -e "${BLUE}📞 EXTERNAL APIS (OPTIONAL)${NC}"
echo -e "${BLUE}=========================${NC}"

echo -e "${CYAN}These are optional for initial development:${NC}"
echo ""

read -p "Configure Twilio (Voice/SMS)? [y/N]: " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${CYAN}Get credentials from https://console.twilio.com${NC}"
    prompt_config "TWILIO_ACCOUNT_SID" "Twilio Account SID" "" false
    prompt_config "TWILIO_AUTH_TOKEN" "Twilio Auth Token" "" true
    prompt_config "TWILIO_PHONE_NUMBER" "Twilio Phone Number (e.g., +1234567890)" "" false
fi

echo ""
read -p "Configure Change Healthcare API? [y/N]: " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${CYAN}Get credentials from https://developers.changehealthcare.com${NC}"
    prompt_config "CHANGE_HEALTHCARE_API_KEY" "Change Healthcare API Key" "" true
    prompt_config "CHANGE_HEALTHCARE_CLIENT_ID" "Change Healthcare Client ID" "" false
    prompt_config "CHANGE_HEALTHCARE_CLIENT_SECRET" "Change Healthcare Client Secret" "" true
    echo "CHANGE_HEALTHCARE_ENDPOINT=https://api.changehealthcare.com" >> "$TARGET_FILE"
fi

# Add ChromaDB configuration
echo "" >> "$TARGET_FILE"
echo "# ChromaDB Configuration" >> "$TARGET_FILE"
if [[ "$ENVIRONMENT" == "development" ]]; then
    echo "CHROMA_HOST=localhost" >> "$TARGET_FILE"
    echo "CHROMA_PORT=8001" >> "$TARGET_FILE"
    echo "CHROMA_PERSIST_DIRECTORY=./data/chroma_db" >> "$TARGET_FILE"
else
    echo "CHROMA_HOST=greenlightpa-chromadb.fly.dev" >> "$TARGET_FILE"
    echo "CHROMA_PORT=8000" >> "$TARGET_FILE"
    echo "CHROMADB_URL=https://greenlightpa-chromadb.fly.dev" >> "$TARGET_FILE"
fi

echo ""
echo -e "${GREEN}🎉 CONFIGURATION COMPLETE!${NC}"
echo -e "${GREEN}=========================${NC}"

echo ""
echo -e "${YELLOW}📄 Configuration saved to: $TARGET_FILE${NC}"
echo ""

echo -e "${BLUE}🧪 NEXT STEPS:${NC}"
echo ""
echo -e "${CYAN}1. Test the configuration:${NC}"
echo -e "   ${YELLOW}python scripts/test_connections.py${NC}"
echo ""
echo -e "${CYAN}2. Start development environment:${NC}"
if [[ "$ENVIRONMENT" == "development" ]]; then
    echo -e "   ${YELLOW}docker-compose --profile development up -d${NC}"
else
    echo -e "   ${YELLOW}flyctl deploy -a greenlightpa-api${NC}"
fi
echo ""
echo -e "${CYAN}3. Access services:${NC}"
if [[ "$ENVIRONMENT" == "development" ]]; then
    echo -e "   ${YELLOW}FastAPI: http://localhost:8000${NC}"
    echo -e "   ${YELLOW}N8n: http://localhost:5678 (admin / $N8N_PASSWORD)${NC}"
    echo -e "   ${YELLOW}ChromaDB: http://localhost:8001${NC}"
else
    echo -e "   ${YELLOW}FastAPI: https://greenlightpa-api.fly.dev${NC}"
    echo -e "   ${YELLOW}N8n: https://greenlightpa-n8n.fly.dev (admin / $N8N_PASSWORD)${NC}"
    echo -e "   ${YELLOW}ChromaDB: https://greenlightpa-chromadb.fly.dev${NC}"
fi

echo ""
echo -e "${PURPLE}🔐 IMPORTANT SECURITY NOTES:${NC}"
echo -e "${YELLOW}• Keep your API keys secure and never commit them to git${NC}"
echo -e "${YELLOW}• The generated passwords are in $TARGET_FILE - save them securely${NC}"
echo -e "${YELLOW}• For production, consider using a secrets manager${NC}"
echo -e "${YELLOW}• Regularly rotate your API keys and passwords${NC}"

echo ""
echo -e "${GREEN}✅ Setup complete! Ready for Sprint 1: Core AI Pipeline Development${NC}" 