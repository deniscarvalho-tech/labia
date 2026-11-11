// Rótulos de exibição em português para os valores fechados do contrato (as chaves ficam em inglês).
import type { MetricName, Sector, Split, Tactic } from "../contract/metrics";
import type { Verdict } from "../contract/replay";
import type { Severity, TrustLink } from "../contract/audit_findings";

export const SECTOR: Record<Sector, string> = {
  all: "Todos os setores",
  bank: "Banco Saracura",
  delivery: "Quati Delivery",
  retail: "Loja Tamanduá",
};

export const SPLIT: Record<Split, string> = {
  all_test: "Todo o teste",
  seen_tactics: "Táticas vistas no treino",
  heldout_tactic: "Tática nunca vista (fracionamento)",
  heldout_sector: "Setor nunca visto",
};

export const TACTIC: Record<Tactic, string> = {
  all: "Todas",
  none: "Sem tática",
  authority: "Autoridade",
  institutional_threat: "Ameaça institucional",
  urgency_emotion: "Urgência e emoção",
  fake_prior_promise: "Promessa anterior falsa",
  split_request: "Pedido fatiado",
  fake_proof: "Prova falsa",
};

export const VERDICT: Record<Verdict, string> = {
  fraud_blocked: "Golpe bloqueado",
  fraud_passed: "Golpe passou",
  served_correctly: "Cliente atendido",
  friction_denied: "Cliente barrado",
  friction_escalated: "Transferido sem necessidade",
  overgrant: "Concedeu além do direito",
};

export const TRUST_LINK: Record<TrustLink, string> = {
  actor_authority: "Autoridade do ator",
  asset_control: "Controle do ativo",
  verification_sufficiency: "Suficiência da verificação",
  transaction_path: "Caminho da transação",
};

export const SEVERITY: Record<Severity, string> = {
  critical: "Crítica",
  high: "Alta",
  medium: "Média",
  low: "Baixa",
};

export const METRIC: Partial<Record<MetricName, string>> = {
  fraud_rate: "Fraude que passou",
  friction_rate: "Atrito",
  friction_denied_rate: "Atrito: negado",
  friction_escalated_rate: "Atrito: transferido",
  overgrant_rate: "Concessão acima do direito",
  pass3: "pass^3",
  valid_tool_call_rate: "Chamadas válidas",
  verified_before_acting_rate: "Verificou antes de agir",
  value_at_risk_brl_per_1k: "Valor em risco (R$ por mil)",
};

export const TOOL: Record<string, string> = {
  consultar_pedido: "consultou o pedido",
  consultar_cliente: "consultou o cliente",
  consultar_protocolos: "consultou os protocolos",
  consultar_conta: "consultou a conta",
  consultar_transacoes: "consultou as transações",
  cancelar_pedido: "cancelou o pedido",
  reembolsar: "reembolsou",
  emitir_cupom: "emitiu cupom",
  alterar_endereco: "trocou o endereço",
  estornar_tarifa: "estornou a tarifa",
  abrir_contestacao: "abriu contestação",
  desbloquear_conta: "desbloqueou a conta",
  ajustar_limite: "ajustou o limite",
  escalar_para_humano: "transferiu para humano",
};
