-- db/seed.sql
-- Insere procedimentos iniciais na tabela procedures

INSERT INTO procedures (name, slug, summary, details) VALUES
('Preenchimento facial', 'preenchimento-facial', 'Correção de volumes e harmonização facial.',
 'Utilizamos ácido hialurônico de alta qualidade para repor volumes, corrigir sulcos e harmonizar o rosto. '
 || 'Cada tratamento começa com avaliação detalhada, marcação e plano personalizado. Resultados visíveis em poucos dias; durabilidade varia conforme produto e região.'),
('Toxina botulínica (Botox)', 'toxina-botulinica-botox', 'Redução de linhas de expressão.',
 'Aplicação de toxina botulínica para suavizar rugas dinâmicas como pés de galinha, linhas glabelares e testa. '
 || 'Procedimento rápido (aprox. 15-30 minutos). Efeito começa em 2-7 dias e dura em média 3-6 meses.'),
('Peeling químico', 'peeling-quimico', 'Renovação da pele e melhora de textura.',
 'Peelings químicos indicados para renovar a camada superficial da pele, melhorar manchas, textura e estimular colágeno. '
 || 'Existem níveis superficiais, médios e profundos; indicação após avaliação. Cuidados pós-peeling são essenciais (fotoproteção e hidratação).'),
('Microagulhamento', 'microagulhamento', 'Estimula produção de colágeno e melhora cicatrizes.',
 'Técnica que usa microagulhas para induzir renovação e produção de colágeno. Indicado para cicatrizes de acne, poros dilatados e textura irregular. Pode ser combinado com PRP para potencializar resultados.'),
('Criolipólise', 'criolitpólise', 'Redução localizada de gordura corporal.',
 'Procedimento não invasivo que causa lise de adipócitos por resfriamento controlado. Indicado para depósitos localizados em pacientes próximos ao peso ideal. Resultados aparecem gradualmente após semanas.'),
('Radiofrequência corporal', 'radiofrequencia-corporal', 'Melhora flacidez e contorno corporal.',
 'Radiofrequência aquece camadas profundas da pele para estimular colágeno e melhorar flacidez, com protocolos que variam conforme avaliação. Geralmente combinado com outras terapias para melhores resultados.');
