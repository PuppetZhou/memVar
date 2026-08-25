type StatusMessageProps = {
  title: string;
  children: React.ReactNode;
  tone?: "neutral" | "error";
};

export function StatusMessage({ title, children, tone = "neutral" }: StatusMessageProps) {
  return (
    <section className={`status-message ${tone}`} role={tone === "error" ? "alert" : "status"}>
      <h2>{title}</h2>
      <p>{children}</p>
    </section>
  );
}
