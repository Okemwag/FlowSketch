"use client"

import { useState, useEffect } from "react"
import Link from "next/link"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Switch } from "@/components/ui/switch"
import { Separator } from "@/components/ui/separator"
import {
  ArrowRight,
  Zap,
  Shield,
  Users,
  Check,
  Star,
  Sparkles,
  Database,
  Globe,
  Headphones,
  Twitter,
  Github,
  Linkedin,
  Mail,
} from "lucide-react"

export default function LandingPage() {
  const [terminalText, setTerminalText] = useState("")
  const [showCursor, setShowCursor] = useState(true)
  const [isYearly, setIsYearly] = useState(false)

  const commands = [
    "$ npm install @saas-platform/cli",
    "$ saas-platform init my-project",
    "$ saas-platform deploy --production",
    "✓ Deployment successful!",
  ]

  const pricingPlans = [
    {
      name: "Starter",
      description: "Perfect for individuals and small teams",
      monthlyPrice: 29,
      yearlyPrice: 290,
      features: ["Up to 5 team members", "10GB storage", "Basic integrations", "Email support", "Mobile app access"],
      popular: false,
    },
    {
      name: "Professional",
      description: "Ideal for growing businesses",
      monthlyPrice: 79,
      yearlyPrice: 790,
      features: [
        "Up to 25 team members",
        "100GB storage",
        "Advanced integrations",
        "Priority support",
        "Custom workflows",
        "Analytics dashboard",
        "API access",
      ],
      popular: true,
    },
    {
      name: "Enterprise",
      description: "For large organizations",
      monthlyPrice: 199,
      yearlyPrice: 1990,
      features: [
        "Unlimited team members",
        "1TB storage",
        "All integrations",
        "24/7 phone support",
        "Custom development",
        "Advanced security",
        "Dedicated account manager",
        "SLA guarantee",
      ],
      popular: false,
    },
  ]

  useEffect(() => {
    let commandIndex = 0
    let charIndex = 0
    let currentCommand = ""

    const typeCommand = () => {
      if (commandIndex < commands.length) {
        if (charIndex < commands[commandIndex].length) {
          currentCommand += commands[commandIndex][charIndex]
          setTerminalText(currentCommand)
          charIndex++
          setTimeout(typeCommand, 50)
        } else {
          setTimeout(() => {
            currentCommand += "\n"
            setTerminalText(currentCommand)
            commandIndex++
            charIndex = 0
            setTimeout(typeCommand, 500)
          }, 1000)
        }
      }
    }

    const timer = setTimeout(typeCommand, 1000)

    // Cursor blinking
    const cursorTimer = setInterval(() => {
      setShowCursor((prev) => !prev)
    }, 500)

    return () => {
      clearTimeout(timer)
      clearInterval(cursorTimer)
    }
  }, [])

  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add("visible")
          }
        })
      },
      { threshold: 0.1 },
    )

    const elements = document.querySelectorAll(".animate-on-scroll")
    elements.forEach((el) => observer.observe(el))

    return () => observer.disconnect()
  }, [])

  return (
    <div className="min-h-screen bg-background text-foreground">
      {/* Navigation */}
      <nav className="fixed top-0 w-full z-50 border-b border-border bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="font-serif text-xl font-bold">SaaS Platform</div>
            <div className="hidden md:flex items-center gap-6">
              <Link href="#features" className="font-sans text-sm hover:text-purple-400 transition-colors">
                Features
              </Link>
              <Link href="#pricing" className="font-sans text-sm hover:text-purple-400 transition-colors">
                Pricing
              </Link>
              <Link href="#about" className="font-sans text-sm hover:text-purple-400 transition-colors">
                About
              </Link>
            </div>
            <div className="flex items-center gap-4">
              <Button variant="ghost" asChild className="font-sans">
                <Link href="/login">Sign in</Link>
              </Button>
              <Button asChild className="bg-purple-600 hover:bg-purple-700 text-white font-sans">
                <Link href="/signup">Get Started</Link>
              </Button>
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="relative overflow-hidden pt-20">
        <div className="absolute inset-0 bg-gradient-to-br from-purple-900/20 via-background to-background" />
        <div className="relative container mx-auto px-4 py-20 lg:py-32">
          <div className="grid lg:grid-cols-2 gap-12 items-center">
            <div className="space-y-8 animate-on-scroll">
              <Badge variant="secondary" className="w-fit animate-pulse">
                🚀 Now in Beta
              </Badge>
              <div className="space-y-4">
                <h1 className="font-serif text-4xl lg:text-6xl font-bold leading-tight">
                  Unlock the Future of{" "}
                  <span className="text-purple-400 bg-gradient-to-r from-purple-400 to-pink-400 bg-clip-text text-transparent">
                    Productivity
                  </span>
                </h1>
                <p className="text-xl text-muted-foreground font-sans leading-relaxed">
                  Seamless integrations and powerful tools at your fingertips. Transform your workflow with our
                  cutting-edge SaaS platform.
                </p>
              </div>
              <div className="flex flex-col sm:flex-row gap-4">
                <Button
                  size="lg"
                  asChild
                  className="bg-purple-600 hover:bg-purple-700 text-white font-sans transform hover:scale-105 transition-all duration-200"
                >
                  <Link href="/signup">
                    Get Started
                    <ArrowRight className="ml-2 h-4 w-4" />
                  </Link>
                </Button>
                <Button
                  size="lg"
                  variant="outline"
                  className="font-sans bg-transparent hover:bg-purple-600/10 transition-all duration-200"
                >
                  Learn More
                </Button>
              </div>
            </div>

            {/* Terminal Animation */}
            <div className="relative animate-on-scroll">
              <Card className="bg-gray-900 border-gray-700 p-6 font-mono text-sm transform hover:scale-105 transition-transform duration-300">
                <div className="flex items-center gap-2 mb-4">
                  <div className="w-3 h-3 rounded-full bg-red-500 animate-pulse" />
                  <div
                    className="w-3 h-3 rounded-full bg-yellow-500 animate-pulse"
                    style={{ animationDelay: "0.2s" }}
                  />
                  <div className="w-3 h-3 rounded-full bg-green-500 animate-pulse" style={{ animationDelay: "0.4s" }} />
                  <span className="ml-4 text-gray-400">Terminal</span>
                </div>
                <div className="min-h-[200px] text-green-400">
                  <pre className="whitespace-pre-wrap">
                    {terminalText}
                    {showCursor && <span className="bg-green-400 text-gray-900">_</span>}
                  </pre>
                </div>
              </Card>
            </div>
          </div>
        </div>
      </section>

      {/* Trusted By Section */}
      <section className="py-16 border-t border-border">
        <div className="container mx-auto px-4">
          <div className="text-center mb-12 animate-on-scroll">
            <p className="text-muted-foreground font-sans">Trusted by innovative companies worldwide</p>
          </div>
          <div className="flex flex-wrap justify-center items-center gap-8 opacity-50">
            {["TechCorp", "InnovateLab", "FutureWorks", "DataFlow", "CloudSync"].map((company, index) => (
              <div
                key={company}
                className="text-2xl font-bold hover:opacity-100 transition-all duration-300 cursor-pointer hover:text-purple-400 animate-on-scroll"
                style={{ animationDelay: `${index * 0.1}s` }}
              >
                {company}
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section id="features" className="py-20">
        <div className="container mx-auto px-4">
          <div className="text-center mb-16 animate-on-scroll">
            <h2 className="font-serif text-3xl lg:text-4xl font-bold mb-4">Powerful Features for Modern Teams</h2>
            <p className="text-xl text-muted-foreground font-sans max-w-2xl mx-auto">
              Everything you need to streamline your workflow and boost productivity
            </p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
            {[
              {
                icon: <Zap className="h-8 w-8 text-purple-400" />,
                title: "Lightning Fast",
                description:
                  "Automate your workflow effortlessly with our high-performance tools and real-time processing.",
              },
              {
                icon: <Users className="h-8 w-8 text-purple-400" />,
                title: "Team Collaboration",
                description:
                  "Collaborate in real-time with your team across any device or platform with seamless sync.",
              },
              {
                icon: <Shield className="h-8 w-8 text-purple-400" />,
                title: "Enterprise Security",
                description:
                  "Secure your data with enterprise-level encryption, compliance, and advanced access controls.",
              },
              {
                icon: <Database className="h-8 w-8 text-purple-400" />,
                title: "Smart Analytics",
                description: "Get actionable insights with advanced analytics and customizable reporting dashboards.",
              },
              {
                icon: <Globe className="h-8 w-8 text-purple-400" />,
                title: "Global Scale",
                description: "Deploy worldwide with our global infrastructure and CDN for optimal performance.",
              },
              {
                icon: <Sparkles className="h-8 w-8 text-purple-400" />,
                title: "AI-Powered",
                description:
                  "Leverage artificial intelligence to automate tasks and provide intelligent recommendations.",
              },
            ].map((feature, index) => (
              <Card
                key={index}
                className="p-6 hover:shadow-xl transition-all duration-300 hover:scale-105 animate-on-scroll border-border group hover:border-purple-500/50"
                style={{ animationDelay: `${index * 0.1}s` }}
              >
                <div className="mb-4 transform group-hover:scale-110 transition-transform duration-200">
                  {feature.icon}
                </div>
                <h3 className="font-serif text-xl font-bold mb-2 group-hover:text-purple-400 transition-colors">
                  {feature.title}
                </h3>
                <p className="text-muted-foreground font-sans">{feature.description}</p>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* Pricing Section */}
      <section id="pricing" className="py-20 bg-muted/30">
        <div className="container mx-auto px-4">
          <div className="text-center mb-16 animate-on-scroll">
            <h2 className="font-serif text-3xl lg:text-4xl font-bold mb-4">Simple, Transparent Pricing</h2>
            <p className="text-xl text-muted-foreground font-sans max-w-2xl mx-auto mb-8">
              Choose the perfect plan for your team. No hidden fees, no surprises.
            </p>

            <div className="flex items-center justify-center gap-4 mb-8">
              <span
                className={`font-sans transition-colors ${!isYearly ? "text-foreground" : "text-muted-foreground"}`}
              >
                Monthly
              </span>
              <Switch checked={isYearly} onCheckedChange={setIsYearly} className="data-[state=checked]:bg-purple-600" />
              <span className={`font-sans transition-colors ${isYearly ? "text-foreground" : "text-muted-foreground"}`}>
                Yearly
                <Badge variant="secondary" className="ml-2 text-xs animate-bounce">
                  Save 20%
                </Badge>
              </span>
            </div>
          </div>

          <div className="grid md:grid-cols-3 gap-8 max-w-6xl mx-auto">
            {pricingPlans.map((plan, index) => (
              <Card
                key={index}
                className={`relative p-8 hover:shadow-xl transition-all duration-500 animate-on-scroll group ${
                  plan.popular
                    ? "border-purple-500 shadow-lg scale-105 bg-card hover:scale-110"
                    : "border-border hover:scale-105 hover:border-purple-500/30"
                }`}
                style={{ animationDelay: `${index * 0.2}s` }}
              >
                {plan.popular && (
                  <div className="absolute -top-4 left-1/2 transform -translate-x-1/2">
                    <Badge className="bg-purple-600 text-white px-4 py-1 animate-pulse">
                      <Star className="w-3 h-3 mr-1" />
                      Most Popular
                    </Badge>
                  </div>
                )}

                <div className="text-center mb-8">
                  <h3 className="font-serif text-2xl font-bold mb-2 group-hover:text-purple-400 transition-colors">
                    {plan.name}
                  </h3>
                  <p className="text-muted-foreground font-sans mb-4">{plan.description}</p>
                  <div className="mb-4">
                    <span className="text-4xl font-bold transition-all duration-300">
                      ${isYearly ? Math.floor(plan.yearlyPrice / 12) : plan.monthlyPrice}
                    </span>
                    <span className="text-muted-foreground font-sans">/month</span>
                    {isYearly && (
                      <div className="text-sm text-muted-foreground">Billed annually (${plan.yearlyPrice})</div>
                    )}
                  </div>
                </div>

                <ul className="space-y-3 mb-8">
                  {plan.features.map((feature, featureIndex) => (
                    <li
                      key={featureIndex}
                      className="flex items-center gap-3 font-sans group-hover:text-foreground transition-colors"
                    >
                      <Check className="h-4 w-4 text-purple-400 flex-shrink-0" />
                      <span className="text-sm">{feature}</span>
                    </li>
                  ))}
                </ul>

                <Button
                  asChild
                  className={`w-full font-sans transition-all duration-200 ${
                    plan.popular
                      ? "bg-purple-600 hover:bg-purple-700 text-white hover:scale-105"
                      : "bg-transparent border border-border hover:bg-purple-600 hover:text-white hover:border-purple-600"
                  }`}
                >
                  <Link href="/signup">{plan.popular ? "Start Free Trial" : "Get Started"}</Link>
                </Button>
              </Card>
            ))}
          </div>

          <div className="text-center mt-12 animate-on-scroll">
            <p className="text-muted-foreground font-sans mb-4">
              All plans include a 14-day free trial. No credit card required.
            </p>
            <Button
              variant="outline"
              className="font-sans bg-transparent hover:bg-purple-600/10 hover:border-purple-600 transition-all duration-200"
            >
              <Headphones className="mr-2 h-4 w-4" />
              Contact Sales
            </Button>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 bg-purple-900/10">
        <div className="container mx-auto px-4 text-center animate-on-scroll">
          <h2 className="font-serif text-3xl lg:text-4xl font-bold mb-4">Ready to Transform Your Workflow?</h2>
          <p className="text-xl text-muted-foreground font-sans mb-8 max-w-2xl mx-auto">
            Join thousands of teams already using our platform to boost their productivity
          </p>
          <Button
            size="lg"
            asChild
            className="bg-purple-600 hover:bg-purple-700 text-white font-sans transform hover:scale-105 transition-all duration-200"
          >
            <Link href="/signup">
              Start Free Trial
              <ArrowRight className="ml-2 h-4 w-4" />
            </Link>
          </Button>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-background border-t border-border">
        <div className="container mx-auto px-4 py-16">
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8 mb-12">
            <div className="space-y-4">
              <div className="font-serif text-xl font-bold">SaaS Platform</div>
              <p className="text-muted-foreground font-sans text-sm leading-relaxed">
                Unlock the future of productivity with seamless integrations and powerful tools designed for modern
                teams.
              </p>
              <div className="flex space-x-4">
                <Button variant="ghost" size="sm" className="p-2 hover:text-purple-400 transition-colors">
                  <Twitter className="h-4 w-4" />
                </Button>
                <Button variant="ghost" size="sm" className="p-2 hover:text-purple-400 transition-colors">
                  <Github className="h-4 w-4" />
                </Button>
                <Button variant="ghost" size="sm" className="p-2 hover:text-purple-400 transition-colors">
                  <Linkedin className="h-4 w-4" />
                </Button>
                <Button variant="ghost" size="sm" className="p-2 hover:text-purple-400 transition-colors">
                  <Mail className="h-4 w-4" />
                </Button>
              </div>
            </div>

            <div className="space-y-4">
              <h3 className="font-serif font-semibold">Product</h3>
              <ul className="space-y-2 font-sans text-sm">
                <li>
                  <Link href="#features" className="text-muted-foreground hover:text-purple-400 transition-colors">
                    Features
                  </Link>
                </li>
                <li>
                  <Link href="#pricing" className="text-muted-foreground hover:text-purple-400 transition-colors">
                    Pricing
                  </Link>
                </li>
                <li>
                  <Link href="/integrations" className="text-muted-foreground hover:text-purple-400 transition-colors">
                    Integrations
                  </Link>
                </li>
                <li>
                  <Link href="/api" className="text-muted-foreground hover:text-purple-400 transition-colors">
                    API
                  </Link>
                </li>
                <li>
                  <Link href="/changelog" className="text-muted-foreground hover:text-purple-400 transition-colors">
                    Changelog
                  </Link>
                </li>
              </ul>
            </div>

            <div className="space-y-4">
              <h3 className="font-serif font-semibold">Company</h3>
              <ul className="space-y-2 font-sans text-sm">
                <li>
                  <Link href="/about" className="text-muted-foreground hover:text-purple-400 transition-colors">
                    About
                  </Link>
                </li>
                <li>
                  <Link href="/careers" className="text-muted-foreground hover:text-purple-400 transition-colors">
                    Careers
                  </Link>
                </li>
                <li>
                  <Link href="/blog" className="text-muted-foreground hover:text-purple-400 transition-colors">
                    Blog
                  </Link>
                </li>
                <li>
                  <Link href="/press" className="text-muted-foreground hover:text-purple-400 transition-colors">
                    Press
                  </Link>
                </li>
                <li>
                  <Link href="/contact" className="text-muted-foreground hover:text-purple-400 transition-colors">
                    Contact
                  </Link>
                </li>
              </ul>
            </div>

            <div className="space-y-4">
              <h3 className="font-serif font-semibold">Support</h3>
              <ul className="space-y-2 font-sans text-sm">
                <li>
                  <Link href="/help" className="text-muted-foreground hover:text-purple-400 transition-colors">
                    Help Center
                  </Link>
                </li>
                <li>
                  <Link href="/docs" className="text-muted-foreground hover:text-purple-400 transition-colors">
                    Documentation
                  </Link>
                </li>
                <li>
                  <Link href="/status" className="text-muted-foreground hover:text-purple-400 transition-colors">
                    Status
                  </Link>
                </li>
                <li>
                  <Link href="/security" className="text-muted-foreground hover:text-purple-400 transition-colors">
                    Security
                  </Link>
                </li>
                <li>
                  <Link href="/privacy" className="text-muted-foreground hover:text-purple-400 transition-colors">
                    Privacy
                  </Link>
                </li>
              </ul>
            </div>
          </div>

          <Separator className="mb-8" />

          <div className="flex flex-col md:flex-row justify-between items-center gap-4">
            <div className="text-muted-foreground font-sans text-sm">© 2024 SaaS Platform. All rights reserved.</div>
            <div className="flex gap-6 font-sans text-sm">
              <Link href="/terms" className="text-muted-foreground hover:text-purple-400 transition-colors">
                Terms
              </Link>
              <Link href="/privacy" className="text-muted-foreground hover:text-purple-400 transition-colors">
                Privacy
              </Link>
              <Link href="/cookies" className="text-muted-foreground hover:text-purple-400 transition-colors">
                Cookies
              </Link>
            </div>
          </div>
        </div>
      </footer>
    </div>
  )
}
