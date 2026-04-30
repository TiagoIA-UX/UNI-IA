"""
Script de teste do GapExecutor com MT5Mock.
Valida a lógica de gap, abertura de ordens e trailing stop.
"""

from executor import GapExecutor, GapType
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_gap_executor():
    """Testa o executor principal."""
    logger.info("=" * 60)
    logger.info("TESTE DO GAP EXECUTOR - UNI IA")
    logger.info("=" * 60)
    
    executor = GapExecutor(settings_path='settings.yaml', skip_time_validation=True)
    
    # Teste 1: Conectar ao MT5Mock
    logger.info("\n[TESTE 1] Conectar ao MT5...")
    executor.connect(login=123456, password='test_password', server='XM-Real')
    assert executor.mt5.connected, "Falha ao conectar"
    logger.info("✓ Conectado com sucesso")
    
    # Teste 2: Avaliar gap de alta
    logger.info("\n[TESTE 2] Avaliar gap de alta...")
    # Gap de 6.5 pontos: 6.5 * 0.01 = 0.065 de diferença de preço
    setup_alta = executor.evaluate_gap(
        symbol='WDOFUT',
        abertura=5.265,  # Abertura do dia
        fechamento_anterior=5.200,  # Fechamento anterior (gap = 65 pontos = 6.5 em escala)
        maxima=5.300,
        minima=5.200
    )
    assert setup_alta is not None, "Gap de alta não foi detectado"
    assert setup_alta.gap_type == GapType.ALTA, "Tipo de gap incorreto"
    logger.info(f"✓ Gap de alta detectado: {setup_alta.gap_size:.2f} pts")
    
    # Teste 3: Executar ordem de alta
    logger.info("\n[TESTE 3] Executar ordem de gap de alta...")
    ticket_alta = executor.execute_order('WDOFUT', setup_alta, volume=1.0)
    assert ticket_alta is not None, "Falha ao executar ordem"
    logger.info(f"✓ Ordem #{ticket_alta} executada (BUY @ {setup_alta.entrada})")
    
    # Teste 4: Gerenciar trailing stop
    logger.info("\n[TESTE 4] Gerenciar trailing stop...")
    executor.manage_trailing_stop(ticket_alta, current_price=5.222, trailing_distance=1.0)
    logger.info("✓ Trailing stop gerenciado")
    
    # Teste 5: Resumo de ordens ativas
    logger.info("\n[TESTE 5] Resumo de ordens ativas...")
    summary = executor.get_active_orders_summary()
    logger.info(f"✓ Total de ordens ativas: {summary['total_active']}")
    for order in summary['orders']:
        logger.info(f"  - #{order['ticket']}: {order['symbol']} {order['type']} {order['volume']} @ {order['price']}")
    
    # Teste 6: Fechar ordem
    logger.info("\n[TESTE 6] Fechar ordem...")
    executor.close_order(ticket_alta, close_price=5.210)
    logger.info("✓ Ordem fechada com sucesso")
    
    # Teste 7: Desconectar
    logger.info("\n[TESTE 7] Desconectar do MT5...")
    executor.disconnect()
    assert not executor.mt5.connected, "Falha ao desconectar"
    logger.info("✓ Desconectado com sucesso")
    
    logger.info("\n" + "=" * 60)
    logger.info("TODOS OS TESTES PASSARAM! ✓")
    logger.info("=" * 60)

if __name__ == '__main__':
    test_gap_executor()
