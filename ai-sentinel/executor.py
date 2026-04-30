import yaml
import os
from datetime import datetime, time
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Mock MT5 para testes locais
class MT5Mock:
    """Mock de MetaTrader5 para simulação local sem terminal instalado."""
    
    ORDER_TYPE_BUY = 0
    ORDER_TYPE_SELL = 1
    ORDER_STATE_PLACED = 0
    ORDER_STATE_FILLED = 1
    
    def __init__(self):
        self.connected = False
        self.orders = {}
        self.order_counter = 1
        
    def initialize(self, path=None, login=None, password=None, server=None, timeout=None, portable=False):
        """Simula inicialização do MT5."""
        self.connected = True
        logger.info(f"MT5Mock inicializado: login={login}, server={server}")
        return True
    
    def shutdown(self):
        """Simula desligamento do MT5."""
        self.connected = False
        logger.info("MT5Mock desligado")
        return True
    
    def open_order(self, symbol, order_type, volume, price, sl, tp, deviation=20, magic=0, comment="", type_time=None, type_filling=None):
        """Simula abertura de ordem."""
        if not self.connected:
            logger.error("MT5 não conectado")
            return None
        
        order_id = self.order_counter
        self.order_counter += 1
        
        order_data = {
            'ticket': order_id,
            'symbol': symbol,
            'type': order_type,
            'volume': volume,
            'price': price,
            'sl': sl,
            'tp': tp,
            'state': self.ORDER_STATE_FILLED,
            'open_time': datetime.now(),
            'current_price': price,
            'profit': 0.0,
            'trailing_stop_active': False,
            'trailing_distance': 0.0,
        }
        
        self.orders[order_id] = order_data
        logger.info(f"Ordem #{order_id} aberta: {symbol} {order_type} {volume} @ {price}")
        return order_id
    
    def order_modify(self, ticket, price, sl, tp):
        """Simula modificação de ordem."""
        if ticket not in self.orders:
            logger.error(f"Ordem #{ticket} não encontrada")
            return False
        
        self.orders[ticket]['price'] = price
        self.orders[ticket]['sl'] = sl
        self.orders[ticket]['tp'] = tp
        logger.info(f"Ordem #{ticket} modificada: SL={sl}, TP={tp}")
        return True
    
    def order_close(self, ticket, volume, price, deviation=20):
        """Simula fechamento de ordem."""
        if ticket not in self.orders:
            logger.error(f"Ordem #{ticket} não encontrada")
            return False
        
        order = self.orders.pop(ticket)
        logger.info(f"Ordem #{ticket} fechada @ {price}, Lucro: {order['profit']}")
        return True
    
    def positions_get(self, symbol=None):
        """Retorna posições abertas."""
        if symbol:
            return [o for o in self.orders.values() if o['symbol'] == symbol]
        return list(self.orders.values())
    
    def symbol_info_tick(self, symbol):
        """Simula obtenção de tick atual do símbolo."""
        return {
            'last': 5.300,
            'bid': 5.298,
            'ask': 5.302,
        }


class GapType(Enum):
    """Tipos de gaps."""
    ALTA = "ALTA"
    BAIXA = "BAIXA"


@dataclass
class GapSetup:
    """Representa um setup de gap."""
    gap_type: GapType
    abertura: float
    fechamento_dia_anterior: float
    entrada: float
    target: float
    stop: float
    gap_size: float
    data: datetime


class GapExecutor:
    """Executor principal de estratégia de gaps em modo Hedge."""
    
    def __init__(self, settings_path='settings.yaml', skip_time_validation=False):
        """Inicializa o executor com parâmetros do settings.yaml."""
        self.settings = self._load_settings(settings_path)
        self.mt5 = MT5Mock()  # Usar mock localmente; em produção usar: import MetaTrader5 as mt5
        self.active_orders = {}
        self.skip_time_validation = skip_time_validation
        
    def _load_settings(self, settings_path: str) -> Dict:
        """Carrega parâmetros do settings.yaml."""
        if not os.path.exists(settings_path):
            logger.error(f"Arquivo {settings_path} não encontrado")
            return {}
        
        with open(settings_path, 'r') as f:
            settings = yaml.safe_load(f)
        
        logger.info(f"Settings carregados: pGap={settings.get('pGap')}, pEntrada={settings.get('pEntrada')}, pStop={settings.get('pStop')}")
        return settings
    
    def connect(self, login: int, password: str, server: str):
        """Conecta ao MT5."""
        success = self.mt5.initialize(login=login, password=password, server=server)
        if success:
            logger.info("Conectado ao MT5 com sucesso")
        else:
            logger.error("Falha ao conectar ao MT5")
        return success
    
    def disconnect(self):
        """Desconecta do MT5."""
        self.mt5.shutdown()
        logger.info("Desconectado do MT5")
    
    def _is_within_trading_hours(self) -> bool:
        """Verifica se está dentro do horário de entrada permitido."""
        if self.skip_time_validation:
            return True
        
        h_limite = self.settings.get('pHLimiteEntrada', '12:00')
        h_final = self.settings.get('pHFinal', '16:30')
        
        hora_limite = datetime.strptime(h_limite, '%H:%M').time()
        hora_final = datetime.strptime(h_final, '%H:%M').time()
        hora_atual = datetime.now().time()
        
        return hora_limite <= hora_atual < hora_final
    
    def evaluate_gap(self, symbol: str, abertura: float, fechamento_anterior: float, maxima: float, minima: float) -> Optional[GapSetup]:
        """Avalia se há um gap elegível para operação."""
        p_gap = self.settings.get('pGap', 5.0)
        p_entrada = self.settings.get('pEntrada', 1.0)
        p_stop = self.settings.get('pStop', 1.5)
        
        # Calcular gap em pontos (1 ponto = 0.01 em WDOFUT)
        gap_price = abertura - fechamento_anterior
        gap_size = gap_price * 100  # Converter para pontos
        
        # Filtro: apenas gaps >= pGap pontos
        if abs(gap_size) < p_gap:
            logger.info(f"{symbol}: Gap de {gap_size:.2f} pts < pGap ({p_gap}). Descartado.")
            return None
        
        # Filtro: horário de entrada
        if not self._is_within_trading_hours():
            logger.warning(f"{symbol}: Fora do horário de entrada permitido.")
            return None
        
        if gap_size > 0:  # Gap de Alta
            entrada = abertura + (p_entrada * 0.01)
            target = fechamento_anterior
            stop = entrada + (p_stop * 0.01)
            return GapSetup(
                gap_type=GapType.ALTA,
                abertura=abertura,
                fechamento_dia_anterior=fechamento_anterior,
                entrada=entrada,
                target=target,
                stop=stop,
                gap_size=gap_size,
                data=datetime.now()
            )
        else:  # Gap de Baixa
            entrada = abertura - (p_entrada * 0.01)
            target = fechamento_anterior
            stop = entrada - (p_stop * 0.01)
            return GapSetup(
                gap_type=GapType.BAIXA,
                abertura=abertura,
                fechamento_dia_anterior=fechamento_anterior,
                entrada=entrada,
                target=target,
                stop=stop,
                gap_size=abs(gap_size),
                data=datetime.now()
            )
    
    def execute_order(self, symbol: str, setup: GapSetup, volume: float = 1.0) -> Optional[int]:
        """Executa ordem baseada no setup de gap."""
        if setup.gap_type == GapType.ALTA:
            order_type = self.mt5.ORDER_TYPE_BUY
            order_price = setup.entrada
            order_sl = setup.stop
            order_tp = setup.target
        else:
            order_type = self.mt5.ORDER_TYPE_SELL
            order_price = setup.entrada
            order_sl = setup.stop
            order_tp = setup.target
        
        ticket = self.mt5.open_order(
            symbol=symbol,
            order_type=order_type,
            volume=volume,
            price=order_price,
            sl=order_sl,
            tp=order_tp,
            comment=f"Gap {setup.gap_type.value} - {setup.data.strftime('%Y-%m-%d %H:%M:%S')}"
        )
        
        if ticket:
            self.active_orders[ticket] = {
                'symbol': symbol,
                'setup': setup,
                'volume': volume,
                'trailing_stop_active': False,
                'trailing_distance': 0.0,
            }
            logger.info(f"Ordem #{ticket} executada: {symbol} {setup.gap_type.value} @ {order_price}")
            return ticket
        else:
            logger.error(f"Falha ao executar ordem para {symbol}")
            return None
    
    def manage_trailing_stop(self, ticket: int, current_price: float, trailing_distance: float = 1.0):
        """Gerencia trailing stop para uma ordem."""
        if ticket not in self.active_orders:
            logger.warning(f"Ordem #{ticket} não encontrada no rastreamento.")
            return
        
        order_info = self.active_orders[ticket]
        setup = order_info['setup']
        
        # Calcular profit em pontos
        if setup.gap_type == GapType.ALTA:
            profit = current_price - setup.entrada
            new_sl = current_price - trailing_distance
        else:
            profit = setup.entrada - current_price
            new_sl = current_price + trailing_distance
        
        if profit > 1.5:  # Ativar trailing após 1.5 pontos de lucro
            if not order_info['trailing_stop_active']:
                logger.info(f"Ordem #{ticket}: Trailing Stop ativado (Lucro: {profit:.2f} pts)")
                order_info['trailing_stop_active'] = True
            
            # Atualizar SL se for mais favorável
            current_sl = setup.stop
            if setup.gap_type == GapType.ALTA and new_sl > current_sl:
                self.mt5.order_modify(ticket, setup.entrada, new_sl, setup.target)
                logger.info(f"Ordem #{ticket}: SL atualizado para {new_sl:.2f}")
            elif setup.gap_type == GapType.BAIXA and new_sl < current_sl:
                self.mt5.order_modify(ticket, setup.entrada, new_sl, setup.target)
                logger.info(f"Ordem #{ticket}: SL atualizado para {new_sl:.2f}")
    
    def close_order(self, ticket: int, close_price: float):
        """Fecha uma ordem."""
        if ticket in self.active_orders:
            self.mt5.order_close(ticket, self.active_orders[ticket]['volume'], close_price)
            del self.active_orders[ticket]
            logger.info(f"Ordem #{ticket} fechada @ {close_price}")
    
    def get_active_orders_summary(self) -> Dict:
        """Retorna resumo das ordens ativas."""
        positions = self.mt5.positions_get()
        return {
            'total_active': len(positions),
            'orders': [
                {
                    'ticket': p['ticket'],
                    'symbol': p['symbol'],
                    'type': 'BUY' if p['type'] == self.mt5.ORDER_TYPE_BUY else 'SELL',
                    'volume': p['volume'],
                    'price': p['price'],
                    'sl': p['sl'],
                    'tp': p['tp'],
                    'profit': p['profit'],
                }
                for p in positions
            ]
        }


if __name__ == '__main__':
    # Teste local do executor
    executor = GapExecutor(settings_path='settings.yaml')
    executor.connect(login=12345, password='password', server='XM-Real')
    
    # Simular análise de gap
    setup = executor.evaluate_gap(
        symbol='WDOFUT',
        abertura=5.220,
        fechamento_anterior=5.207,
        maxima=5.262,
        minima=5.205
    )
    
    if setup:
        logger.info(f"Setup elegível: {setup.gap_type.value} de {setup.gap_size:.2f} pts")
        ticket = executor.execute_order('WDOFUT', setup, volume=1.0)
        
        if ticket:
            # Simular gerenciamento de trailing stop
            executor.manage_trailing_stop(ticket, current_price=5.222, trailing_distance=1.0)
            
            # Resumo de ordens ativas
            summary = executor.get_active_orders_summary()
            logger.info(f"Resumo: {summary['total_active']} ordem(ns) ativa(s)")
    
    executor.disconnect()
