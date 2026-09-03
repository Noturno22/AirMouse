import React from 'react';
import {
  ActivityIndicator,
  Modal,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from 'react-native';

import type { ProEntitlement } from '../hooks/useProEntitlement';

interface Props {
  entitlement: ProEntitlement;
  onClose: () => void;
}

export default function ProGate({ entitlement, onClose }: Props) {
  const { product, purchasing, actionError, purchasePro, restorePro } =
    entitlement;

  const price = product?.displayPrice ?? '';

  return (
    <Modal transparent animationType="fade" visible onRequestClose={onClose}>
      <View style={styles.backdrop}>
        <View style={styles.card}>
          <Text style={styles.eyebrow}>Mãouse</Text>
          <Text style={styles.title}>Desbloqueia o controlo completo</Text>
          <Text style={styles.subtitle}>
            O nível gratuito só permite navegar e pré-visualizar gestos. O Pro
            pago único ativa o controlo real: toque, clique, scroll, voltar,
            início e notificações.
          </Text>

          <View style={styles.priceRow}>
            <Text style={styles.price}>
              {price ? `${price} · compra única` : '· compra única'}
            </Text>
          </View>

          {actionError ? (
            <Text style={styles.error}>{actionError}</Text>
          ) : null}

          <TouchableOpacity
            style={styles.buyButton}
            onPress={purchasePro}
            disabled={purchasing}
          >
            {purchasing ? (
              <ActivityIndicator color="#FFF" />
            ) : (
              <Text style={styles.buyText}>
                {price ? `Comprar Pro (${price})` : 'Comprar Pro'}
              </Text>
            )}
          </TouchableOpacity>

          <TouchableOpacity
            style={styles.restoreButton}
            onPress={restorePro}
            disabled={purchasing}
          >
            <Text style={styles.restoreText}>Restaurar compra</Text>
          </TouchableOpacity>

          <TouchableOpacity style={styles.freeButton} onPress={onClose}>
            <Text style={styles.freeText}>Continuar versão gratuita</Text>
          </TouchableOpacity>
        </View>
      </View>
    </Modal>
  );
}

const styles = StyleSheet.create({
  backdrop: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.85)',
    justifyContent: 'center',
    alignItems: 'center',
    padding: 24,
  },
  card: {
    backgroundColor: '#1f1f1f',
    borderRadius: 20,
    padding: 24,
    width: '100%',
    maxWidth: 420,
  },
  eyebrow: {
    color: '#50C8FF',
    fontSize: 13,
    fontWeight: '700',
    letterSpacing: 1,
    marginBottom: 8,
  },
  title: {
    color: '#FFF',
    fontSize: 24,
    fontWeight: 'bold',
    lineHeight: 30,
    marginBottom: 12,
  },
  subtitle: {
    color: '#CCC',
    fontSize: 15,
    lineHeight: 21,
    marginBottom: 16,
  },
  priceRow: {
    marginBottom: 20,
  },
  price: {
    color: '#5ADC5A',
    fontSize: 16,
    fontWeight: '600',
  },
  error: {
    color: '#FF6B6B',
    fontSize: 14,
    marginBottom: 12,
  },
  buyButton: {
    backgroundColor: '#50C8FF',
    borderRadius: 12,
    paddingVertical: 14,
    alignItems: 'center',
    marginBottom: 12,
  },
  buyText: {
    color: '#FFF',
    fontSize: 16,
    fontWeight: '700',
  },
  restoreButton: {
    paddingVertical: 12,
    alignItems: 'center',
    marginBottom: 8,
  },
  restoreText: {
    color: '#AAA',
    fontSize: 14,
  },
  freeButton: {
    paddingVertical: 10,
    alignItems: 'center',
  },
  freeText: {
    color: '#777',
    fontSize: 14,
  },
});
