import React from 'react'
import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import { Music, Heart, Mail, Phone, MapPin, Facebook, Twitter, Instagram, Youtube } from 'lucide-react'

const Footer: React.FC = () => {
  const currentYear = new Date().getFullYear()

  const footerLinks = {
    learning: [
      { name: 'Sarali Varisai', nameDevanagari: 'सरली वरिसै', href: '/exercises/sarali' },
      { name: 'Janta Varisai', nameDevanagari: 'जंता वरिसै', href: '/exercises/janta' },
      { name: 'Alankaram', nameDevanagari: 'अलंकारम्', href: '/exercises/alankaram' },
      { name: 'Ragas', nameDevanagari: 'राग', href: '/ragas' }
    ],
    community: [
      { name: 'Practice Groups', nameDevanagari: 'अभ्यास समूह', href: '/community/groups' },
      { name: 'Forums', nameDevanagari: 'मंच', href: '/community/forums' },
      { name: 'Events', nameDevanagari: 'कार्यक्रम', href: '/community/events' },
      { name: 'Teachers', nameDevanagari: 'शिक्षक', href: '/teachers' }
    ],
    support: [
      { name: 'Help Center', nameDevanagari: 'सहायता केंद्र', href: '/help' },
      { name: 'Contact Us', nameDevanagari: 'संपर्क', href: '/contact' },
      { name: 'FAQ', nameDevanagari: 'प्रश्न', href: '/faq' },
      { name: 'Feedback', nameDevanagari: 'प्रतिक्रिया', href: '/feedback' }
    ],
    legal: [
      { name: 'Privacy Policy', nameDevanagari: 'गोपनीयता', href: '/privacy' },
      { name: 'Terms of Service', nameDevanagari: 'नियम', href: '/terms' },
      { name: 'Cookie Policy', nameDevanagari: 'कुकी नीति', href: '/cookies' },
      { name: 'Copyright', nameDevanagari: 'कॉपीराइट', href: '/copyright' }
    ]
  }

  const socialLinks = [
    { name: 'Facebook', icon: Facebook, href: 'https://facebook.com', color: 'hover:text-blue-600' },
    { name: 'Twitter', icon: Twitter, href: 'https://twitter.com', color: 'hover:text-sky-500' },
    { name: 'Instagram', icon: Instagram, href: 'https://instagram.com', color: 'hover:text-pink-600' },
    { name: 'YouTube', icon: Youtube, href: 'https://youtube.com', color: 'hover:text-red-600' }
  ]

  return (
    <footer className="bg-gradient-to-t from-gray-900 via-gray-800 to-gray-900 text-white">
      {/* Main Footer */}
      <div className="container mx-auto px-4 py-12">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-8">
          {/* Brand */}
          <div className="lg:col-span-1">
            <div className="flex items-center space-x-3 mb-4">
              <div className="w-10 h-10 bg-gradient-to-br from-orange-500 to-red-500 rounded-lg flex items-center justify-center shadow-lg">
                <Music className="h-6 w-6 text-white" />
              </div>
              <div>
                <h3 className="text-xl font-bold bg-gradient-to-r from-orange-400 to-red-400 bg-clip-text text-transparent">
                  संगीत शाला
                </h3>
                <p className="text-sm text-gray-400">Carnatic Learning</p>
              </div>
            </div>

            <p className="text-gray-300 text-sm mb-6 leading-relaxed">
              Traditional Carnatic music learning platform combining ancient wisdom with modern technology.
              Master the art of Indian classical music through structured practice and personalized guidance.
            </p>

            {/* Contact Info */}
            <div className="space-y-2 text-sm text-gray-400">
              <div className="flex items-center space-x-2">
                <Mail className="h-4 w-4" />
                <span>support@sangeetshaala.com</span>
              </div>
              <div className="flex items-center space-x-2">
                <Phone className="h-4 w-4" />
                <span>+91 (555) 123-4567</span>
              </div>
              <div className="flex items-center space-x-2">
                <MapPin className="h-4 w-4" />
                <span>Chennai, Tamil Nadu, India</span>
              </div>
            </div>
          </div>

          {/* Learning */}
          <div>
            <h4 className="text-lg font-semibold mb-4 text-orange-400">Learning</h4>
            <ul className="space-y-2">
              {footerLinks.learning.map((link) => (
                <li key={link.href}>
                  <Link
                    to={link.href}
                    className="text-gray-300 hover:text-orange-400 transition-colors text-sm group"
                  >
                    <div>{link.name}</div>
                    <div className="text-xs text-gray-500 group-hover:text-orange-300">
                      {link.nameDevanagari}
                    </div>
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          {/* Community */}
          <div>
            <h4 className="text-lg font-semibold mb-4 text-orange-400">Community</h4>
            <ul className="space-y-2">
              {footerLinks.community.map((link) => (
                <li key={link.href}>
                  <Link
                    to={link.href}
                    className="text-gray-300 hover:text-orange-400 transition-colors text-sm group"
                  >
                    <div>{link.name}</div>
                    <div className="text-xs text-gray-500 group-hover:text-orange-300">
                      {link.nameDevanagari}
                    </div>
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          {/* Support */}
          <div>
            <h4 className="text-lg font-semibold mb-4 text-orange-400">Support</h4>
            <ul className="space-y-2">
              {footerLinks.support.map((link) => (
                <li key={link.href}>
                  <Link
                    to={link.href}
                    className="text-gray-300 hover:text-orange-400 transition-colors text-sm group"
                  >
                    <div>{link.name}</div>
                    <div className="text-xs text-gray-500 group-hover:text-orange-300">
                      {link.nameDevanagari}
                    </div>
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          {/* Newsletter */}
          <div>
            <h4 className="text-lg font-semibold mb-4 text-orange-400">Stay Connected</h4>
            <p className="text-gray-300 text-sm mb-4">
              Subscribe to our newsletter for the latest updates, tips, and learning resources.
            </p>

            <div className="space-y-3">
              <div className="flex">
                <input
                  type="email"
                  placeholder="Enter your email"
                  className="flex-1 px-3 py-2 bg-gray-700 border border-gray-600 rounded-l-lg text-sm focus:outline-none focus:border-orange-500 focus:bg-gray-600 transition-colors"
                />
                <button className="px-4 py-2 bg-gradient-to-r from-orange-500 to-red-500 text-white rounded-r-lg hover:from-orange-600 hover:to-red-600 transition-all duration-200 text-sm font-medium">
                  Subscribe
                </button>
              </div>

              {/* Social Links */}
              <div className="flex space-x-3 pt-2">
                {socialLinks.map((social) => (
                  <motion.a
                    key={social.name}
                    href={social.href}
                    target="_blank"
                    rel="noopener noreferrer"
                    whileHover={{ scale: 1.1 }}
                    whileTap={{ scale: 0.95 }}
                    className={`p-2 bg-gray-700 rounded-lg text-gray-400 ${social.color} transition-all duration-200 hover:bg-gray-600`}
                  >
                    <social.icon className="h-4 w-4" />
                  </motion.a>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Bottom Bar */}
      <div className="border-t border-gray-700">
        <div className="container mx-auto px-4 py-6">
          <div className="flex flex-col md:flex-row items-center justify-between space-y-4 md:space-y-0">
            <div className="flex items-center space-x-1 text-sm text-gray-400">
              <span>© {currentYear} संगीत शाला (Sangeet Shaala). Made with</span>
              <Heart className="h-4 w-4 text-red-500" />
              <span>for preserving Indian classical music tradition.</span>
            </div>

            <div className="flex flex-wrap items-center space-x-6 text-sm">
              {footerLinks.legal.map((link, index) => (
                <React.Fragment key={link.href}>
                  <Link
                    to={link.href}
                    className="text-gray-400 hover:text-orange-400 transition-colors"
                  >
                    {link.name}
                  </Link>
                  {index < footerLinks.legal.length - 1 && (
                    <span className="text-gray-600">•</span>
                  )}
                </React.Fragment>
              ))}
            </div>
          </div>
        </div>
      </div>
    </footer>
  )
}

export default Footer