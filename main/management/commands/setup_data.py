from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from main.models import CyberCrime, ChatbotConfig
import uuid

User = get_user_model()

class Command(BaseCommand):
    help = 'Set up initial data for CySafe application'

    def handle(self, *args, **options):
        self.stdout.write('Setting up initial data for CySafe...')
        
        # Create admin user
        self.create_admin_user()
        
        # Create sample cyber crimes
        self.create_sample_crimes()
        
        # Create chatbot config
        self.create_chatbot_config()
        
        self.stdout.write(self.style.SUCCESS('Successfully set up initial data!'))

    def create_admin_user(self):
        try:
            admin_user = User.objects.create_user(
                username='admin',
                email='cybersafeadmin@deepcytes.uk.in',
                password='CySafeAdmin2024!',
                is_staff=True,
                is_superuser=True
            )
            self.stdout.write(f'Created admin user: {admin_user.email}')
        except Exception as e:
            self.stdout.write(f'Admin user already exists or error: {e}')

    def create_sample_crimes(self):
        sample_crimes = [
            {
                'type': 'Phishing Email Scam',
                'description': 'Fraudulent emails that appear to be from legitimate organizations to steal sensitive information like passwords, credit card numbers, and personal data.',
                'category': 'email_fraud',
                'severity': 'high',
                'prevention_tips': [
                    'Never click on suspicious links in emails',
                    'Verify sender email addresses carefully',
                    'Don\'t share personal information via email',
                    'Use two-factor authentication',
                    'Report suspicious emails to your IT department'
                ],
                'reporting_steps': [
                    'Take screenshots of the phishing email',
                    'Forward the email to your IT security team',
                    'Report to cybercrime.gov.in',
                    'Change passwords if you clicked any links',
                    'Monitor your accounts for suspicious activity'
                ]
            },
            {
                'type': 'UPI Payment Fraud',
                'description': 'Scammers create fake UPI payment links or QR codes to steal money from victims\' bank accounts.',
                'category': 'financial_fraud',
                'severity': 'critical',
                'prevention_tips': [
                    'Never share UPI PIN with anyone',
                    'Verify payment requests independently',
                    'Use official banking apps only',
                    'Enable transaction alerts',
                    'Check payment details carefully'
                ],
                'reporting_steps': [
                    'Immediately block your UPI ID',
                    'Contact your bank to freeze transactions',
                    'File complaint with cybercrime.gov.in',
                    'Report to your bank\'s fraud department',
                    'Keep all transaction details for investigation'
                ]
            },
            {
                'type': 'Social Media Account Hacking',
                'description': 'Unauthorized access to social media accounts to steal personal information or spread malicious content.',
                'category': 'personal_data',
                'severity': 'medium',
                'prevention_tips': [
                    'Use strong, unique passwords',
                    'Enable two-factor authentication',
                    'Be careful with third-party apps',
                    'Regularly review account activity',
                    'Log out from shared devices'
                ],
                'reporting_steps': [
                    'Immediately change your password',
                    'Enable two-factor authentication',
                    'Report to the social media platform',
                    'Check for unauthorized posts or messages',
                    'Monitor for identity theft signs'
                ]
            },
            {
                'type': 'Online Job Scam',
                'description': 'Fake job offers that require upfront payments or personal information for non-existent positions.',
                'category': 'job_fraud',
                'severity': 'high',
                'prevention_tips': [
                    'Research the company thoroughly',
                    'Never pay money for job applications',
                    'Be suspicious of high-paying remote jobs',
                    'Verify job offers through official channels',
                    'Don\'t share personal documents without verification'
                ],
                'reporting_steps': [
                    'Stop all communication with the scammer',
                    'Report to cybercrime.gov.in',
                    'Contact the real company if impersonated',
                    'Monitor your bank accounts',
                    'Report to job portals if applicable'
                ]
            },
            {
                'type': 'Ransomware Attack',
                'description': 'Malicious software that encrypts files and demands payment to restore access to the victim\'s data.',
                'category': 'system_attack',
                'severity': 'critical',
                'prevention_tips': [
                    'Keep software and systems updated',
                    'Use reliable antivirus software',
                    'Regularly backup important data',
                    'Be cautious with email attachments',
                    'Don\'t click on suspicious links'
                ],
                'reporting_steps': [
                    'Disconnect from the internet immediately',
                    'Don\'t pay the ransom',
                    'Contact cybersecurity experts',
                    'Report to cybercrime.gov.in',
                    'Restore from clean backups if available'
                ]
            },
            {
                'type': 'Cyberbullying and Harassment',
                'description': 'Online harassment, threats, or bullying through social media, messaging apps, or other digital platforms.',
                'category': 'harassment',
                'severity': 'high',
                'prevention_tips': [
                    'Block and report harassers',
                    'Don\'t respond to threatening messages',
                    'Keep evidence of harassment',
                    'Use privacy settings on social media',
                    'Talk to trusted friends or family'
                ],
                'reporting_steps': [
                    'Document all harassment with screenshots',
                    'Block the harasser on all platforms',
                    'Report to the platform\'s safety team',
                    'File complaint with cybercrime.gov.in',
                    'Contact local police if threats are serious'
                ]
            }
        ]

        for crime_data in sample_crimes:
            try:
                crime = CyberCrime.objects.create(
                    id=uuid.uuid4(),
                    type=crime_data['type'],
                    description=crime_data['description'],
                    category=crime_data['category'],
                    severity=crime_data['severity'],
                    prevention_tips=crime_data['prevention_tips'],
                    reporting_steps=crime_data['reporting_steps']
                )
                self.stdout.write(f'Created crime: {crime.type}')
            except Exception as e:
                self.stdout.write(f'Error creating crime {crime_data["type"]}: {e}')

    def create_chatbot_config(self):
        try:
            config = ChatbotConfig.objects.create(
                gemini_model='gemini-2.5-pro',
                system_prompt="You are CyberSafe AI Assistant, an expert cybersecurity advisor. Provide helpful, accurate information about cyber threats, prevention tips, and reporting procedures. Always prioritize user safety and direct them to official channels when needed."
            )
            self.stdout.write('Created chatbot configuration')
        except Exception as e:
            self.stdout.write(f'Chatbot config already exists or error: {e}') 