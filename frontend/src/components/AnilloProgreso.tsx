/** Anillo de progreso del panel. El valor va de 0 a 100. */
export function AnilloProgreso({ valor, tamano = 132 }: { valor: number; tamano?: number }) {
  const acotado = Math.min(100, Math.max(0, valor))
  const grosor = 12
  const radio = (tamano - grosor) / 2
  const circunferencia = 2 * Math.PI * radio

  return (
    <div className="anillo">
      <svg width={tamano} height={tamano} role="img" aria-label={`Cumplimiento ${acotado}%`}>
        <circle className="anillo-pista" cx={tamano / 2} cy={tamano / 2} r={radio} strokeWidth={grosor} />
        <circle
          className="anillo-valor"
          cx={tamano / 2}
          cy={tamano / 2}
          r={radio}
          strokeWidth={grosor}
          strokeDasharray={circunferencia}
          strokeDashoffset={circunferencia * (1 - acotado / 100)}
        />
      </svg>
      <span className="anillo-cifra numero">{acotado}%</span>
    </div>
  )
}
