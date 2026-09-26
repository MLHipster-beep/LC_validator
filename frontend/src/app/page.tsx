import { FileSearch, Gauge, ScanText, ShieldCheck } from "lucide-react"
import { PilotForm } from "@/components/pilot-form"
import { ThemeToggle } from "@/components/theme-toggle"
import { Validator } from "@/components/validator"
import { buttonVariants } from "@/components/ui/button"

const FEATURES = [
  {
    icon: ScanText,
    title: "Reads any scan",
    body: "Gemini Vision extracts SWIFT MT700 fields and invoice data from PDFs and photos, with OCR clean-up for numbers.",
  },
  {
    icon: FileSearch,
    title: "Auto-classifies",
    body: "Separates the issued LC from drafts and bank instructions, plus invoices, BOLs, packing lists and more.",
  },
  {
    icon: ShieldCheck,
    title: "Rule-based checks",
    body: "Deterministic engine checks amounts, quantity tolerance, beneficiary, HS code, PAN, EXIM code, signature and stamp.",
  },
  {
    icon: Gauge,
    title: "Severity scoring",
    body: "Every discrepancy is graded Critical, High or Low and rolled into a single bank-readiness score.",
  },
]

function Logo() {
  return (
    <div className="flex items-center gap-2">
      <div className="flex size-6 items-center justify-center rounded-md bg-foreground text-background">
        <ShieldCheck className="size-3.5" />
      </div>
      <span className="text-sm font-semibold tracking-tight">LC Validator</span>
    </div>
  )
}

export default function Home() {
  return (
    <>
      <header className="sticky top-0 z-40 border-b bg-background/80 backdrop-blur-md">
        <div className="mx-auto flex h-14 max-w-6xl items-center justify-between px-4 sm:px-6">
          <Logo />
          <nav className="flex items-center gap-1">
            <a href="#how" className={buttonVariants({ variant: "ghost", size: "sm" })}>
              How it works
            </a>
            <a href="#pilot" className={buttonVariants({ variant: "ghost", size: "sm" })}>
              Pilot access
            </a>
            <a
              href="https://github.com/MLHipster-beep/LC_validator"
              target="_blank"
              rel="noreferrer"
              aria-label="GitHub repository"
              className={buttonVariants({ variant: "ghost", size: "icon-sm" })}
            >
              <svg viewBox="0 0 24 24" className="size-4" fill="currentColor" aria-hidden>
                <path d="M12 .5C5.73.5.75 5.48.75 11.75c0 4.97 3.22 9.18 7.69 10.67.56.1.77-.24.77-.54v-1.9c-3.13.68-3.79-1.51-3.79-1.51-.51-1.3-1.25-1.65-1.25-1.65-1.02-.7.08-.69.08-.69 1.13.08 1.72 1.16 1.72 1.16 1 1.72 2.64 1.22 3.28.93.1-.73.39-1.22.71-1.5-2.5-.28-5.13-1.25-5.13-5.57 0-1.23.44-2.24 1.16-3.03-.12-.28-.5-1.43.11-2.98 0 0 .95-.3 3.1 1.16a10.8 10.8 0 0 1 5.64 0c2.15-1.46 3.1-1.16 3.1-1.16.61 1.55.23 2.7.11 2.98.72.79 1.16 1.8 1.16 3.03 0 4.33-2.64 5.28-5.15 5.56.4.35.76 1.03.76 2.08v3.08c0 .3.2.65.78.54 4.46-1.49 7.68-5.7 7.68-10.67C23.25 5.48 18.27.5 12 .5Z" />
              </svg>
            </a>
            <ThemeToggle />
          </nav>
        </div>
      </header>

      <main className="flex-1">
        {/* Hero */}
        <section className="relative overflow-hidden border-b">
          <div
            aria-hidden
            className="pointer-events-none absolute inset-0 [background-image:linear-gradient(to_right,var(--border)_1px,transparent_1px),linear-gradient(to_bottom,var(--border)_1px,transparent_1px)] [background-size:44px_44px] [mask-image:radial-gradient(ellipse_at_top,black_30%,transparent_70%)] opacity-60"
          />
          <div className="relative mx-auto max-w-6xl px-4 pt-16 pb-12 sm:px-6 sm:pt-24">
            <div className="mx-auto max-w-2xl text-center">
              <span className="inline-flex items-center gap-2 rounded-full border bg-background px-3 py-1 text-xs text-muted-foreground">
                <span className="size-1.5 rounded-full bg-emerald-500" />
                Built for Nepali exporters · UCP 600 aware
              </span>
              <h1 className="mt-6 text-4xl font-semibold tracking-tight text-balance sm:text-5xl">
                Catch LC discrepancies <span className="text-muted-foreground">before the bank does.</span>
              </h1>
              <p className="mx-auto mt-4 max-w-xl text-base text-pretty text-muted-foreground">
                Upload your Letter of Credit and Commercial Invoice. Get a severity-graded discrepancy report in under a
                minute, and avoid rejection fees and payment delays.
              </p>
            </div>
          </div>
        </section>

        {/* App */}
        <section className="mx-auto grid max-w-6xl gap-6 px-4 py-10 sm:px-6 lg:grid-cols-[1fr_340px]">
          <Validator />
          <aside className="space-y-4 lg:sticky lg:top-20 lg:self-start">
            <PilotForm />
            <p className="px-1 text-xs leading-relaxed text-muted-foreground">
              Documents are processed in memory and are not stored. Results are advisory. Always confirm with your bank
              before presentation.
            </p>
          </aside>
        </section>

        {/* How it works */}
        <section id="how" className="border-t bg-muted/30">
          <div className="mx-auto max-w-6xl px-4 py-16 sm:px-6">
            <h2 className="text-2xl font-semibold tracking-tight">How it works</h2>
            <p className="mt-2 max-w-xl text-sm text-muted-foreground">
              AI handles messy extraction. A deterministic rules engine makes the compliance decision, so results are
              explainable and repeatable.
            </p>
            <div className="mt-8 grid gap-px overflow-hidden rounded-xl border bg-border sm:grid-cols-2 lg:grid-cols-4">
              {FEATURES.map(({ icon: Icon, title, body }) => (
                <div key={title} className="bg-background p-5">
                  <Icon className="size-5 text-muted-foreground" />
                  <h3 className="mt-4 text-sm font-medium">{title}</h3>
                  <p className="mt-1.5 text-sm leading-relaxed text-muted-foreground">{body}</p>
                </div>
              ))}
            </div>
          </div>
        </section>
      </main>

      <footer className="border-t">
        <div className="mx-auto flex max-w-6xl flex-col items-center justify-between gap-2 px-4 py-6 text-xs text-muted-foreground sm:flex-row sm:px-6">
          <Logo />
          <p>Built by Aditya · Next.js, FastAPI &amp; Gemini</p>
        </div>
      </footer>
    </>
  )
}
