"use client"

import { Loader2, Send } from "lucide-react"
import { useState, type FormEvent } from "react"
import { toast } from "sonner"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { submitLead } from "@/lib/api"

export function PilotForm() {
  const [pending, setPending] = useState(false)

  async function onSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault()
    const formEl = e.currentTarget
    const data = new FormData(formEl)
    const payload = {
      name: String(data.get("name") ?? "").trim(),
      phone: String(data.get("phone") ?? "").trim(),
      message: String(data.get("message") ?? "").trim(),
    }
    if (!payload.phone) {
      toast.error("Please add your WhatsApp number.")
      return
    }

    setPending(true)
    try {
      await submitLead(payload)
      toast.success("Thanks! We'll reach out on WhatsApp soon.")
      formEl.reset()
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Something went wrong.")
    } finally {
      setPending(false)
    }
  }

  return (
    <Card id="pilot">
      <CardHeader>
        <CardTitle>Request pilot access</CardTitle>
        <CardDescription>For exporters, banks and freight forwarders in Nepal.</CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={onSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="name">Name / Company</Label>
            <Input id="name" name="name" placeholder="Himalayan Handicrafts Pvt. Ltd." autoComplete="organization" />
          </div>
          <div className="space-y-2">
            <Label htmlFor="phone">WhatsApp number</Label>
            <Input id="phone" name="phone" type="tel" placeholder="+977 98XXXXXXXX" required autoComplete="tel" />
          </div>
          <div className="space-y-2">
            <Label htmlFor="message">What do you need?</Label>
            <Textarea id="message" name="message" rows={3} placeholder="e.g. BOL checks, bulk uploads, bank-ready PDF reports…" />
          </div>
          <Button type="submit" className="w-full" disabled={pending}>
            {pending ? <Loader2 className="animate-spin" /> : <Send />}
            {pending ? "Sending…" : "Request access"}
          </Button>
        </form>
      </CardContent>
    </Card>
  )
}
