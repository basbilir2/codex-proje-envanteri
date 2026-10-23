function calculateTip(amount, rate) {
  const value = Number(amount);
  const percent = Number(rate);
  if (!Number.isFinite(value) || !Number.isFinite(percent) || value < 0 || percent < 0) return null;
  const tip = Math.round(value * percent) / 100;
  const total = Math.round((value + tip) * 100) / 100;
  return { tip, total };
}

if (typeof document !== 'undefined') {
  const amount = document.querySelector('#amount');
  const rate = document.querySelector('#rate');
  const result = document.querySelector('#result');
  document.querySelector('#calculate').addEventListener('click', () => {
    const calculated = calculateTip(amount.value, rate.value);
    result.textContent = calculated
      ? `Bahşiş: ${calculated.tip.toFixed(2)} TL · Toplam: ${calculated.total.toFixed(2)} TL`
      : 'Lütfen geçerli, sıfır veya daha büyük değerler girin.';
  });
}

if (typeof module !== 'undefined') module.exports = { calculateTip };
