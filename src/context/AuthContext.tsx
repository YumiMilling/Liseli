import { createContext, useContext, useEffect, useState, useCallback } from 'react'
import type { ReactNode } from 'react'
import type { User } from '@supabase/supabase-js'
import { supabase } from '@/lib/supabase'
import type { Contributor, ZamLanguage } from '@/types'

interface AuthState {
  user: User | null
  contributor: Contributor | null
  loading: boolean
  signUp: (email: string, password: string, profile: {
    handle: string
    languages: ZamLanguage[]
    province: string
  }) => Promise<void>
  signIn: (email: string, password: string) => Promise<void>
  signOut: () => Promise<void>
}

const AuthContext = createContext<AuthState | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [contributor, setContributor] = useState<Contributor | null>(null)
  const [loading, setLoading] = useState(true)

  const fetchContributor = useCallback(async (authId: string) => {
    const { data } = await supabase
      .from('contributors')
      .select('*')
      .eq('auth_id', authId)
      .single()
    setContributor(data)
  }, [])

  useEffect(() => {
    supabase.auth.getSession().then(({ data: { session } }) => {
      setUser(session?.user ?? null)
      if (session?.user) {
        fetchContributor(session.user.id)
      }
      setLoading(false)
    })

    const { data: { subscription } } = supabase.auth.onAuthStateChange(
      (_event, session) => {
        setUser(session?.user ?? null)
        if (session?.user) {
          fetchContributor(session.user.id)
        } else {
          setContributor(null)
        }
      }
    )

    return () => subscription.unsubscribe()
  }, [fetchContributor])

  const signUp = async (
    email: string,
    password: string,
    profile: { handle: string; languages: ZamLanguage[]; province: string }
  ) => {
    const { data: authData, error: authError } = await supabase.auth.signUp({
      email,
      password,
    })
    if (authError) throw authError
    if (!authData.user) throw new Error('Sign up failed')

    const { error: profileError } = await supabase.from('contributors').insert({
      auth_id: authData.user.id,
      handle: profile.handle,
      languages: profile.languages,
      province: profile.province,
    })
    if (profileError) throw profileError

    await fetchContributor(authData.user.id)
  }

  const signIn = async (email: string, password: string) => {
    const { error } = await supabase.auth.signInWithPassword({ email, password })
    if (error) throw error
  }

  const signOut = async () => {
    await supabase.auth.signOut()
    setContributor(null)
  }

  return (
    <AuthContext.Provider value={{ user, contributor, loading, signUp, signIn, signOut }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
